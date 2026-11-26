// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "forge-std/Test.sol";
import "../src/OriginRiskEmitter.sol";
import "../src/ReactiveRiskSentinel.sol";
import "../src/DestinationLiquidatorGuard.sol";

/// @dev Test-only subclass. Lets tests flip the inherited `vm` flag. It is not part of src/.
contract SentinelHarness is ReactiveRiskSentinel {
    constructor(uint256 a, address b, uint256 c, address d) ReactiveRiskSentinel(a, b, c, d) {}

    function setVmForTesting(bool _vm) external {
        require(msg.sender == deployer, "Only deployer");
        vm = _vm;
    }
}

contract ReactiveRiskSentinelTest is Test {
    OriginRiskEmitter public originEmitter;
    SentinelHarness public sentinel;
    DestinationLiquidatorGuard public guard;

    address public constant CALLBACK_RELAYER = address(0xCAFE);
    address public constant RVM_ID = address(0xA11CE);
    address public constant VAULT_OWNER = address(0xBEEF);
    uint256 public constant ORIGIN_CHAIN_ID = 1001;
    uint256 public constant DEST_CHAIN_ID = 1001;

    event Callback(
        uint256 indexed chain_id,
        address indexed _contract,
        uint64 indexed gas_limit,
        bytes payload
    );

    function setUp() public {
        originEmitter = new OriginRiskEmitter();

        vm.prank(RVM_ID);
        guard = new DestinationLiquidatorGuard(CALLBACK_RELAYER);

        sentinel = new SentinelHarness(
            ORIGIN_CHAIN_ID,
            address(originEmitter),
            DEST_CHAIN_ID,
            address(guard)
        );
        sentinel.setVmForTesting(true);
    }

    function _makeAlertRecord(
        uint256 vaultId,
        uint256 currentRatio,
        uint256 minRatio,
        uint256 actionCode
    ) internal view returns (IReactive.LogRecord memory) {
        return IReactive.LogRecord({
            chain_id: ORIGIN_CHAIN_ID,
            _contract: address(originEmitter),
            topic_0: uint256(sentinel.ALERT_TOPIC_0()),
            topic_1: vaultId,
            topic_2: uint256(uint160(VAULT_OWNER)),
            topic_3: 0,
            data: abi.encode(currentRatio, minRatio, actionCode),
            block_number: 1000,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function test_react_triggers_callback_when_ratio_under_threshold() public {
        uint256 vaultId = 101;
        uint256 currentRatio = 11000;
        uint256 minRatio = 12500;
        uint256 actionCode = 1;

        IReactive.LogRecord memory record = _makeAlertRecord(vaultId, currentRatio, minRatio, actionCode);

        bytes memory expectedPayload = abi.encodeWithSignature(
            "executeDefensiveActionWithNonce(address,uint256,address,uint256,uint256)",
            address(0),
            vaultId,
            VAULT_OWNER,
            actionCode,
            uint256(1)
        );

        vm.expectEmit(true, true, true, true);
        emit Callback(
            DEST_CHAIN_ID,
            address(guard),
            sentinel.CALLBACK_GAS_LIMIT(),
            expectedPayload
        );

        sentinel.react(record);

        assertEq(sentinel.alertsProcessed(), 1);
        assertEq(sentinel.callbacksTriggered(), 1);
        assertEq(sentinel.callbackNonce(), 1);
    }

    function test_react_ignores_safe_ratio() public {
        IReactive.LogRecord memory record = _makeAlertRecord(102, 15000, 12500, 1);

        sentinel.react(record);

        assertEq(sentinel.alertsProcessed(), 1);
        assertEq(sentinel.callbacksTriggered(), 0);
        assertEq(sentinel.callbackNonce(), 0);
    }

    function test_react_ignores_unrelated_event_topics() public {
        bytes32 dummyTopic = keccak256("DummyEvent(uint256)");
        IReactive.LogRecord memory record = IReactive.LogRecord({
            chain_id: ORIGIN_CHAIN_ID,
            _contract: address(originEmitter),
            topic_0: uint256(dummyTopic),
            topic_1: 0,
            topic_2: 0,
            topic_3: 0,
            data: "",
            block_number: 1002,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });

        sentinel.react(record);

        assertEq(sentinel.alertsProcessed(), 0);
        assertEq(sentinel.callbacksTriggered(), 0);
    }

    function test_origin_emitter_rejects_non_guardian() public {
        vm.prank(address(0xBAD));
        vm.expectRevert("Only guardian");
        originEmitter.emitRiskAlert(101, VAULT_OWNER, 11000, 12500, 1);
    }

    function test_reactive_sentinel_rejects_non_deployer_set_vm() public {
        vm.prank(address(0xBAD));
        vm.expectRevert("Only deployer");
        sentinel.setVmForTesting(false);

        vm.prank(address(0xBAD));
        vm.expectRevert("Only deployer");
        sentinel.setCooldownSeconds(30);
    }

    function test_reactive_sentinel_increments_callback_nonce() public {
        IReactive.LogRecord memory record = _makeAlertRecord(101, 11000, 12500, 1);
        sentinel.react(record);
        sentinel.react(record);

        assertEq(sentinel.callbackNonce(), 2);
        assertEq(sentinel.callbacksTriggered(), 2);
    }

    function test_reactive_sentinel_timestamp_cooldown_blocks_burst_and_allows_after_expiry() public {
        vm.warp(1_700_000_000);
        sentinel.setCooldownSeconds(60);

        IReactive.LogRecord memory record = _makeAlertRecord(101, 11000, 12500, 1);
        sentinel.react(record);
        assertEq(sentinel.callbacksTriggered(), 1);

        // Within 60s window: alert is counted but callback is suppressed
        vm.warp(1_700_000_030);
        sentinel.react(record);
        assertEq(sentinel.alertsProcessed(), 2);
        assertEq(sentinel.callbacksTriggered(), 1);

        // After 60s window expires: callback fires with incremented nonce
        vm.warp(1_700_000_060);
        sentinel.react(record);
        assertEq(sentinel.callbacksTriggered(), 2);
        assertEq(sentinel.callbackNonce(), 2);
    }

    function test_end_to_end_reactive_payload_executes_and_blocks_replay_on_guard() public {
        uint256 vaultId = 303;
        uint256 actionCode = 2;
        IReactive.LogRecord memory record = _makeAlertRecord(vaultId, 10800, 12500, actionCode);

        vm.recordLogs();
        sentinel.react(record);
        Vm.Log[] memory entries = vm.getRecordedLogs();

        bytes memory rawPayload;
        for (uint256 i = 0; i < entries.length; i++) {
            if (entries[i].topics[0] == keccak256("Callback(uint256,address,uint64,bytes)")) {
                rawPayload = abi.decode(entries[i].data, (bytes));
            }
        }
        assertTrue(rawPayload.length > 0);

        // Simulate Reactive relayer injecting RVM_ID into the first address slot
        bytes memory relayerPayload = rawPayload;
        address rvmAddr = RVM_ID;
        assembly {
            // Skip 32-byte length + 4-byte selector; address word starts at offset 36
            mstore(add(relayerPayload, 36), rvmAddr)
        }

        vm.prank(CALLBACK_RELAYER);
        (bool ok1,) = address(guard).call(relayerPayload);
        assertTrue(ok1);
        assertEq(guard.totalRebalances(), 1);

        // Replaying the exact relayer payload must revert due to nonce protection
        vm.prank(CALLBACK_RELAYER);
        (bool ok2,) = address(guard).call(relayerPayload);
        assertFalse(ok2);
        assertEq(guard.totalRebalances(), 1);
    }

    function test_destination_guard_executes_callback_from_authorized_rvm() public {
        vm.prank(CALLBACK_RELAYER);
        guard.executeDefensiveAction(RVM_ID, 101, VAULT_OWNER, 2);

        assertEq(guard.totalRebalances(), 1);
    }

    function test_destination_guard_rejects_unauthorized_rvm() public {
        vm.prank(CALLBACK_RELAYER);
        vm.expectRevert("Authorized RVM ID only");
        guard.executeDefensiveAction(address(0xDEAD), 101, VAULT_OWNER, 2);

        assertEq(guard.totalRebalances(), 0);
    }

    function test_destination_guard_rejects_unauthorized_caller_with_correct_rvm_id() public {
        vm.prank(address(0xBAD));
        vm.expectRevert("Authorized sender only");
        guard.executeDefensiveAction(RVM_ID, 101, VAULT_OWNER, 1);

        assertEq(guard.totalRebalances(), 0);
    }

    function test_destination_guard_nonce_path_rejects_unauthorized_caller() public {
        vm.prank(address(0xBAD));
        vm.expectRevert("Authorized sender only");
        guard.executeDefensiveActionWithNonce(RVM_ID, 101, VAULT_OWNER, 1, 7);

        assertEq(guard.totalRebalances(), 0);
    }

    function test_destination_guard_replay_protection_blocks_duplicate_nonce() public {
        vm.startPrank(CALLBACK_RELAYER);
        guard.executeDefensiveActionWithNonce(RVM_ID, 101, VAULT_OWNER, 1, 42);
        assertEq(guard.totalRebalances(), 1);

        vm.expectRevert("Action already executed");
        guard.executeDefensiveActionWithNonce(RVM_ID, 101, VAULT_OWNER, 1, 42);
        vm.stopPrank();

        assertEq(guard.totalRebalances(), 1);
    }

    function test_fuzz_risk_ratio_evaluation(uint256 currentRatio, uint256 minRatio) public {
        currentRatio = bound(currentRatio, 1, 100000);
        minRatio = bound(minRatio, 1000, 50000);

        IReactive.LogRecord memory record = _makeAlertRecord(1, currentRatio, minRatio, 1);
        sentinel.react(record);

        if (currentRatio < minRatio) {
            assertEq(sentinel.callbacksTriggered(), 1);
        } else {
            assertEq(sentinel.callbacksTriggered(), 0);
        }
    }
}
