// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

/// @title OriginRiskEmitter - Emits DeFi vault collateral risk alerts on origin chains.
/// @notice Deployed on origin chains (e.g., Base Sepolia, Ethereum Sepolia).
contract OriginRiskEmitter {
    event CollateralRatioAlert(
        uint256 indexed vaultId,
        address indexed owner,
        uint256 currentRatio,
        uint256 minRatio,
        uint256 recommendedAction
    );

    address public immutable guardian;

    modifier onlyGuardian() {
        require(msg.sender == guardian, "Only guardian");
        _;
    }

    constructor() {
        guardian = msg.sender;
    }

    /// @notice Emit a collateral ratio alert for a vault.
    /// @param vaultId Unique vault identifier.
    /// @param owner Vault owner address.
    /// @param currentRatio Current collateral ratio in basis points (e.g. 11000 = 110%).
    /// @param minRatio Liquidation threshold in basis points (e.g. 12000 = 120%).
    /// @param recommendedAction Encoded action code (1 = RepayDebt, 2 = SupplyCollateral).
    function emitRiskAlert(
        uint256 vaultId,
        address owner,
        uint256 currentRatio,
        uint256 minRatio,
        uint256 recommendedAction
    ) external onlyGuardian {
        emit CollateralRatioAlert(
            vaultId,
            owner,
            currentRatio,
            minRatio,
            recommendedAction
        );
    }
}
