// SPDX-License-Identifier: MIT
pragma solidity ^0.8.12;

import {Script, console} from "forge-std/Script.sol";
import {ControllerFactory} from "../src/factory.sol";
import {Controller} from "../src/controller.sol";

contract Deploy is Script {
    function run() public {
        // `vm.broadcast` tells Foundry to send the following transactions
        // to the blockchain. The private key comes from your environment.
        vm.startBroadcast();

        // 1. Deploy the ControllerFactory
        ControllerFactory factory = new ControllerFactory();
        console.log("ControllerFactory deployed at:", address(factory));

        // 2. Create the first controller with no referrer
        address firstControllerAddress = factory.createController(address(0));
        console.log("First Controller (no referrer) created at:", firstControllerAddress);

        // 3. Create a second controller that refers to the first one
        address secondControllerAddress = factory.createController(firstControllerAddress);
        console.log("Second Controller (with referrer) created at:", secondControllerAddress);

        // This stops sending transactions.
        vm.stopBroadcast();
    }
}

