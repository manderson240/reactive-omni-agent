// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "forge-std/Script.sol";
import "../src/OriginRiskEmitter.sol";
import "../src/DestinationLiquidatorGuard.sol";

contract DeployOriginAndDestination is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address callbackRelayer = vm.envOr("CALLBACK_RELAYER", address(0));

        vm.startBroadcast(deployerPrivateKey);

        OriginRiskEmitter emitter = new OriginRiskEmitter();
        console.log("OriginRiskEmitter deployed to:", address(emitter));

        DestinationLiquidatorGuard guard = new DestinationLiquidatorGuard(callbackRelayer);
        console.log("DestinationLiquidatorGuard deployed to:", address(guard));

        vm.stopBroadcast();
    }
}
