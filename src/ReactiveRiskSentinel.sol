// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "reactive-lib/abstract-base/AbstractReactive.sol";
import "reactive-lib/interfaces/IReactive.sol";

/// @title ReactiveRiskSentinel - Autonomous Reactive Contract on Reactive Omni (Lasna).
/// @notice Subscribes to origin chain risk alerts, checks safety invariants, and triggers nonce-protected callbacks.
contract ReactiveRiskSentinel is AbstractReactive {
    uint64 public constant CALLBACK_GAS_LIMIT = 250000;

    // CollateralRatioAlert(uint256,address,uint256,uint256,uint256)
    bytes32 public constant ALERT_TOPIC_0 =
        keccak256("CollateralRatioAlert(uint256,address,uint256,uint256,uint256)");

    uint256 public immutable originChainId;
    address public immutable originContract;
    uint256 public immutable destinationChainId;
    address public immutable destinationContract;
    address public immutable deployer;

    uint256 public alertsProcessed;
    uint256 public callbacksTriggered;
    uint256 public callbackNonce;
    uint256 public cooldownSeconds;
    mapping(uint256 => uint256) public lastCallbackTimestamp;

    modifier onlyDeployer() {
        require(msg.sender == deployer, "Only deployer");
        _;
    }

    constructor(
        uint256 _originChainId,
        address _originContract,
        uint256 _destinationChainId,
        address _destinationContract
    ) payable {
        deployer = msg.sender;
        originChainId = _originChainId;
        originContract = _originContract;
        destinationChainId = _destinationChainId;
        destinationContract = _destinationContract;

        if (!vm) {
            // Subscribe on the Reactive Network top level
            service.subscribe(
                _originChainId,
                _originContract,
                uint256(ALERT_TOPIC_0),
                REACTIVE_IGNORE,
                REACTIVE_IGNORE,
                REACTIVE_IGNORE
            );
        }
    }

    /// @notice Process an incoming log record from the origin chain.
    /// @dev Invoked by the ReactVM runtime only. Uses timestamp cooldown and monotonic nonces.
    function react(LogRecord calldata log) external vmOnly {
        if (log.topic_0 != uint256(ALERT_TOPIC_0)) {
            return;
        }

        alertsProcessed++;

        // topic_1: indexed vaultId, topic_2: indexed owner
        uint256 vaultId = log.topic_1;
        address owner = address(uint160(log.topic_2));

        // data contains non-indexed parameters: currentRatio, minRatio, recommendedAction
        (uint256 currentRatio, uint256 minRatio, uint256 recommendedAction) =
            abi.decode(log.data, (uint256, uint256, uint256));

        // Invariant Safety Gate: only trigger if currentRatio is under threshold
        if (currentRatio < minRatio) {
            if (
                cooldownSeconds > 0
                    && lastCallbackTimestamp[vaultId] != 0
                    && block.timestamp < lastCallbackTimestamp[vaultId] + cooldownSeconds
            ) {
                return;
            }

            lastCallbackTimestamp[vaultId] = block.timestamp;
            uint256 nonce = ++callbackNonce;
            callbacksTriggered++;

            // First address slot is reserved for RVM ID injection by the relayer
            bytes memory payload = abi.encodeWithSignature(
                "executeDefensiveActionWithNonce(address,uint256,address,uint256,uint256)",
                address(0),
                vaultId,
                owner,
                recommendedAction,
                nonce
            );

            emit Callback(
                destinationChainId,
                destinationContract,
                CALLBACK_GAS_LIMIT,
                payload
            );
        }
    }

    /// @notice Configure per-vault cooldown window in seconds (timestamp-based for fast L2 origin chains).
    function setCooldownSeconds(uint256 _seconds) external onlyDeployer {
        cooldownSeconds = _seconds;
    }
}
