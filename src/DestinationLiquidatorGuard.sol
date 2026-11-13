// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "reactive-lib/abstract-base/AbstractCallback.sol";

/// @title DestinationLiquidatorGuard - Receives and executes authenticated Reactive callbacks.
/// @notice Deployed on destination chains (e.g., Base Sepolia, Unichain Sepolia).
contract DestinationLiquidatorGuard is AbstractCallback {
    event RebalanceExecuted(
        uint256 indexed vaultId,
        address indexed owner,
        uint256 actionCode,
        uint256 timestamp
    );

    uint256 public totalRebalances;
    mapping(bytes32 => bool) public processedActionIds;

    constructor(address _callbackSender) AbstractCallback(_callbackSender) {}

    /// @notice Callback executed by the Reactive Network relayer.
    /// @param _rvmId The reactive contract instance address that initiated this callback.
    /// @param vaultId The target vault identifier.
    /// @param owner The target vault owner.
    /// @param actionCode Defensive action code executed.
    function executeDefensiveAction(
        address _rvmId,
        uint256 vaultId,
        address owner,
        uint256 actionCode
    ) external rvmIdOnly(_rvmId) {
        totalRebalances++;
        emit RebalanceExecuted(vaultId, owner, actionCode, block.timestamp);
    }

    /// @notice Callback executed with cryptographic nonce replay protection.
    /// @param _rvmId The reactive contract instance address that initiated this callback.
    /// @param vaultId The target vault identifier.
    /// @param owner The target vault owner.
    /// @param actionCode Defensive action code executed.
    /// @param nonce Unique sequence nonce preventing replay attacks.
    function executeDefensiveActionWithNonce(
        address _rvmId,
        uint256 vaultId,
        address owner,
        uint256 actionCode,
        uint256 nonce
    ) external rvmIdOnly(_rvmId) {
        bytes32 actionId = keccak256(
            abi.encodePacked(_rvmId, vaultId, owner, actionCode, nonce)
        );
        require(!processedActionIds[actionId], "Action already executed");
        processedActionIds[actionId] = true;
        totalRebalances++;
        emit RebalanceExecuted(vaultId, owner, actionCode, block.timestamp);
    }
}
