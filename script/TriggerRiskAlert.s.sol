// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "forge-std/Script.sol";
import "../src/OriginRiskEmitter.sol";

contract TriggerRiskAlert is Script {
    function run() external {
        uint256 callerPrivateKey = vm.envUint("PRIVATE_KEY");
        address originContract = vm.envAddress("ORIGIN_CONTRACT");
        uint256 vaultId = vm.envOr("VAULT_ID", uint256(101));
        address owner = vm.envOr("VAULT_OWNER", msg.sender);
        uint256 currentRatio = vm.envOr("CURRENT_RATIO", uint256(11000)); // 110%
        uint256 minRatio = vm.envOr("MIN_RATIO", uint256(12500));         // 125%
        uint256 actionCode = vm.envOr("ACTION_CODE", uint256(1));          // RepayDebt

        vm.startBroadcast(callerPrivateKey);

        OriginRiskEmitter emitter = OriginRiskEmitter(originContract);
        emitter.emitRiskAlert(vaultId, owner, currentRatio, minRatio, actionCode);

        console.log("Risk alert emitted for vault:", vaultId);
        console.log("Current ratio:", currentRatio, "Min ratio:", minRatio);

        vm.stopBroadcast();
    }
}
