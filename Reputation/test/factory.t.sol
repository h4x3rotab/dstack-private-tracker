// SPDX-License-Identifier: MIT
pragma solidity ^0.8.12;

import {Test, console} from "forge-std/Test.sol";
import {ControllerFactory} from "../src/factory.sol";
import {Controller} from "../src/controller.sol";

contract FactoryTest is Test {
    ControllerFactory public factory;
    address public owner; // Represents the first TEE
    address public tee2;  // Represents the second TEE after a "failover"

    function setUp() public {
        // Deploy a new factory before each test
        factory = new ControllerFactory();
        owner = address(this); // Use the test contract as the owner
        tee2 = address(0x2);   // A mock address for the second TEE
    }

    function test_CreateFirstController() public {
        // Create the first controller with no referrer
        address firstControllerAddress = factory.createController(address(0));
        assertTrue(firstControllerAddress != address(0));

        Controller firstController = Controller(firstControllerAddress);
        // Verify the owner is the TEE that called the factory (the test contract)
        assertEq(firstController.owner(), owner);
        // Verify it has no referrer
        assertEq(firstController.referrerController(), address(0));
    }

    function test_CreateChainedController() public {
        // 1. Create the first controller
        address firstControllerAddress = factory.createController(address(0));
        Controller firstController = Controller(firstControllerAddress);

        // 2. Add some data to the first controller as the owner
        firstController.UpdateUser(
            "alice", "salt123", keccak256("pass123"), 100, 50
        );

        // 3. TEE 2 takes over and creates a new controller, referring to the first one
        // We use vm.prank to simulate the call coming from tee2's address
        vm.prank(tee2);
        address secondControllerAddress = factory.createController(firstControllerAddress);
        Controller secondController = Controller(secondControllerAddress);

        // 4. Verify the new controller is owned by tee2 and refers to the first one
        assertEq(secondController.owner(), tee2);
        assertEq(secondController.referrerController(), firstControllerAddress);

        // 5. CRITICAL TEST: Look up "alice" through the new controller
        // It should find the data by chaining the lookup to the first controller.
        Controller.UserData memory aliceData = secondController.getUserData("alice");
        assertEq(aliceData.username, "alice");
        assertEq(aliceData.downloadSize, 100);
        assertEq(aliceData.uploadSize, 50);
    }

    function test_UpdateDataInNewController() public {
        // Setup a chain of two controllers, with "alice" in the first one
        address firstControllerAddress = factory.createController(address(0));
        Controller(firstControllerAddress).UpdateUser(
            "alice", "salt123", keccak256("pass123"), 100, 50
        );
        vm.prank(tee2);
        address secondControllerAddress = factory.createController(firstControllerAddress);
        Controller secondController = Controller(secondControllerAddress);

        // Now, as tee2, update Alice's data. This writes it to the *new* controller
        vm.prank(tee2);
        secondController.UpdateUser(
            "alice", "salt456", keccak256("pass456"), 200, 150
        );

        // Look up the data again through the second controller
        Controller.UserData memory aliceData = secondController.getUserData("alice");
        
        // It should return the NEW data, because it finds it in the second contract first
        assertEq(aliceData.downloadSize, 200);
        assertEq(aliceData.uploadSize, 150);
        assertEq(aliceData.salt, "salt456");
    }
}

