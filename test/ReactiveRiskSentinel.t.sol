// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "forge-std/Test.sol";
import "../src/OriginRiskEmitter.sol";
import "../src/ReactiveRiskSentinel.sol";
import "../src/DestinationLiquidatorGuard.sol";

contract ReactiveRiskSentinelTest is Test {
    OriginRiskEmitter public originEmitter;
    ReactiveRiskSentinel public sentinel;
    DestinationLiquidatorGuard public guard;

    address public constant CALLBACK_RELAYER = address(0xCAFE);
    address public constant VAULT_OWNER = address(0xBEEF);
    uint256 public constant ORIGIN_CHAIN_ID = 1001; // Mock test chain ID
    uint256 public constant DEST_CHAIN_ID = 1001;   // Mock test chain ID

    event Callback(
        uint256 indexed chain_id,
        address indexed _contract,
        uint64 indexed gas_limit,
        bytes payload
    );

    function setUp() public {
        originEmitter = new OriginRiskEmitter();

        // Destination guard deployed on Base Sepolia, trusting CALLBACK_RELAYER
        vm.prank(CALLBACK_RELAYER);
        guard = new DestinationLiquidatorGuard(CALLBACK_RELAYER);

        // Sentinel deployed on Reactive Network
        sentinel = new ReactiveRiskSentinel(
            ORIGIN_CHAIN_ID,
            address(originEmitter),
            DEST_CHAIN_ID,
            address(guard)
        );
        sentinel.setVmForTesting(true);
    }

    function test_react_triggers_callback_when_ratio_under_threshold() public {
        uint256 vaultId = 101;
        uint256 currentRatio = 11000; // 110%
        uint256 minRatio = 12500;     // 125% (under threshold!)
        uint256 actionCode = 1;        // RepayDebt

        bytes memory data = abi.encode(currentRatio, minRatio, actionCode);

        IReactive.LogRecord memory record = IReactive.LogRecord({
            chain_id: ORIGIN_CHAIN_ID,
            _contract: address(originEmitter),
            topic_0: uint256(sentinel.ALERT_TOPIC_0()),
            topic_1: vaultId,
            topic_2: uint256(uint160(VAULT_OWNER)),
            topic_3: 0,
            data: data,
            block_number: 1000,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });

        bytes memory expectedPayload = abi.encodeWithSignature(
            "executeDefensiveAction(address,uint256,address,uint256)",
            address(0),
            vaultId,
            VAULT_OWNER,
            actionCode
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
    }

    function test_react_ignores_safe_ratio() public {
        uint256 vaultId = 102;
        uint256 currentRatio = 15000; // 150%
        uint256 minRatio = 12500;     // 125% (safe!)
        uint256 actionCode = 1;

        bytes memory data = abi.encode(currentRatio, minRatio, actionCode);

        IReactive.LogRecord memory record = IReactive.LogRecord({
            chain_id: ORIGIN_CHAIN_ID,
            _contract: address(originEmitter),
            topic_0: uint256(sentinel.ALERT_TOPIC_0()),
            topic_1: vaultId,
            topic_2: uint256(uint160(VAULT_OWNER)),
            topic_3: 0,
            data: data,
            block_number: 1001,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });

        // No Callback event should be emitted
        sentinel.react(record);

        assertEq(sentinel.alertsProcessed(), 1);
        assertEq(sentinel.callbacksTriggered(), 0);
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

    function test_destination_guard_executes_callback_from_authorized_rvm() public {
        uint256 vaultId = 101;
        uint256 actionCode = 2;

        vm.prank(CALLBACK_RELAYER);
        guard.executeDefensiveAction(CALLBACK_RELAYER, vaultId, VAULT_OWNER, actionCode);

        assertEq(guard.totalRebalances(), 1);
    }

    function test_destination_guard_rejects_unauthorized_rvm() public {
        uint256 vaultId = 101;
        uint256 actionCode = 2;
        address unauthorizedRvm = address(0xDEAD);

        vm.prank(CALLBACK_RELAYER);
        vm.expectRevert("Authorized RVM ID only");
        guard.executeDefensiveAction(unauthorizedRvm, vaultId, VAULT_OWNER, actionCode);

        assertEq(guard.totalRebalances(), 0);
    }

    function test_destination_guard_replay_protection_blocks_duplicate_nonce() public {
        uint256 vaultId = 101;
        uint256 actionCode = 1;
        uint256 nonce = 42;

        vm.startPrank(CALLBACK_RELAYER);
        // First execution succeeds
        guard.executeDefensiveActionWithNonce(CALLBACK_RELAYER, vaultId, VAULT_OWNER, actionCode, nonce);
        assertEq(guard.totalRebalances(), 1);

        // Replay attempt with same nonce must revert
        vm.expectRevert("Action already executed");
        guard.executeDefensiveActionWithNonce(CALLBACK_RELAYER, vaultId, VAULT_OWNER, actionCode, nonce);
        vm.stopPrank();

        assertEq(guard.totalRebalances(), 1);
    }

    function test_fuzz_risk_ratio_evaluation(uint256 currentRatio, uint256 minRatio) public {
        // Bound inputs to realistic 18-decimal or basis point ranges
        currentRatio = bound(currentRatio, 1, 100000);
        minRatio = bound(minRatio, 1000, 50000);

        bytes memory data = abi.encode(currentRatio, minRatio, uint256(1));
        IReactive.LogRecord memory record = IReactive.LogRecord({
            chain_id: ORIGIN_CHAIN_ID,
            _contract: address(originEmitter),
            topic_0: uint256(sentinel.ALERT_TOPIC_0()),
            topic_1: 1,
            topic_2: uint256(uint160(VAULT_OWNER)),
            topic_3: 0,
            data: data,
            block_number: 1000,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });

        sentinel.react(record);

        if (currentRatio < minRatio) {
            assertEq(sentinel.callbacksTriggered(), 1);
        } else {
            assertEq(sentinel.callbacksTriggered(), 0);
        }
    }
}
