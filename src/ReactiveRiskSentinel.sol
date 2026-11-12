// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "reactive-lib/abstract-base/AbstractReactive.sol";
import "reactive-lib/interfaces/IReactive.sol";

/// @title ReactiveRiskSentinel - Autonomous Reactive Contract on Reactive Omni (Lasna).
/// @notice Subscribes to origin chain risk alerts, checks safety invariants, and triggers callbacks.
contract ReactiveRiskSentinel is AbstractReactive {
    uint64 public constant CALLBACK_GAS_LIMIT = 250000;

    // CollateralRatioAlert(uint256,address,uint256,uint256,uint256)
    bytes32 public constant ALERT_TOPIC_0 =
        keccak256("CollateralRatioAlert(uint256,address,uint256,uint256,uint256)");

    uint256 public immutable originChainId;
    address public immutable originContract;
    uint256 public immutable destinationChainId;
    address public immutable destinationContract;

    uint256 public alertsProcessed;
    uint256 public callbacksTriggered;

    constructor(
        uint256 _originChainId,
        address _originContract,
        uint256 _destinationChainId,
        address _destinationContract
    ) payable {
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
    /// @dev Invoked by the ReactVM runtime only.
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

        // Invariant Safety Gate: Only trigger if currentRatio is under the liquidation threshold
        if (currentRatio < minRatio) {
            callbacksTriggered++;

            // First address slot is reserved for RVM ID injection by the relayer
            bytes memory payload = abi.encodeWithSignature(
                "executeDefensiveAction(address,uint256,address,uint256)",
                address(0),
                vaultId,
                owner,
                recommendedAction
            );

            emit Callback(
                destinationChainId,
                destinationContract,
                CALLBACK_GAS_LIMIT,
                payload
            );
        }
    }

    /// @notice Allow manual VM mode override for unit testing in local Foundry.
    function setVmForTesting(bool _vm) external {
        vm = _vm;
    }
}
