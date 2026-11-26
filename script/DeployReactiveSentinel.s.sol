// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "forge-std/Script.sol";
import "../src/ReactiveRiskSentinel.sol";

contract DeployReactiveSentinel is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address originContract = vm.envAddress("ORIGIN_CONTRACT");
        address destinationContract = vm.envAddress("DESTINATION_CONTRACT");
        uint256 originChainId = vm.envUint("ORIGIN_CHAIN_ID");
        uint256 destinationChainId = vm.envUint("DESTINATION_CHAIN_ID");

        vm.startBroadcast(deployerPrivateKey);

        // Deploy Sentinel on Reactive Network (Lasna Testnet)
        // Note: Sentinel may require native gas token for subscriptions
        ReactiveRiskSentinel sentinel = new ReactiveRiskSentinel{value: 0.05 ether}(
            originChainId,
            originContract,
            destinationChainId,
            destinationContract
        );

        console.log("ReactiveRiskSentinel deployed to:", address(sentinel));

        vm.stopBroadcast();
    }
}
