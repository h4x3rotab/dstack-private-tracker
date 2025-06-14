// SPDX-License-Identifier: MIT
pragma solidity ^0.8.12;

// import {Script, console} from "forge-std/Script.sol";
// import {ReputationFactory} from "../src/factory.sol";
// import {Reputation} from "../src/Reputation.sol";

// contract TestLogs is Script {
//     function run() public {
//         vm.startBroadcast();

//         // --- Setup ---
//         console.log("\n--- DEPLOYING CONTRACTS ---");
//         ReputationFactory factory = new ReputationFactory();
//         Reputation Reputation1 = Reputation(factory.createReputation(address(0)));
//         Reputation Reputation2 = Reputation(factory.createReputation(address(Reputation1)));
//         console.log("Reputation 1 Address:", address(Reputation1));
//         console.log("Reputation 2 Address:", address(Reputation2));

//         // --- Add a user to the first Reputation ---
//         console.log("\n--- ADDING 'aviv' TO Reputation 1 ---");
//         Reputation1.UpdateUser("aviv", "salt456", keccak256("pass456"), 200, 100);

//         // --- TEST 1: Check data in Reputation 1 ---
//         console.log("\n--- TEST 1: Calling getUserData for 'aviv' on Reputation 1 ---");
//         Reputation.UserData memory data1 = Reputation1.getUserData("aviv"); // Get and decode data
//         printUserData("Reputation 1 Result", data1);

//         // --- TEST 2: Trigger Migration and check data in Reputation 2 ---
//         console.log("\n--- TEST 2: Calling getUserData for 'aviv' on Reputation 2 (first time) ---");
//         Reputation.UserData memory data2 = Reputation2.getUserData("aviv"); // This will migrate and return the data
//         printUserData("Reputation 2 Result (after migration)", data2);

//         // --- TEST 3: Update data in Reputation 1 ---
//         console.log("\n--- TEST 3: Updating 'aviv' in Reputation 1 ---");
//         Reputation1.UpdateUser("aviv", "newsalt", keccak256("newpass"), 123, 456);

//         console.log("\n--- TEST 3.1: Calling getUserData for 'aviv' on Reputation 1 (second time) ---");
//         Reputation.UserData memory data3 = Reputation1.getUserData("aviv"); // Get the new data
//         printUserData("Reputation 1 Result (after update)", data3);

//         // --- TEST 3.2: Check if Reputation 2 has the OLD, migrated data ---
//         console.log("\n--- TEST 3.2: Calling getUserData for 'aviv' on Reputation 2 (second time) ---");
//         Reputation.UserData memory data4 = Reputation2.getUserData("aviv"); // Should return the data that was already migrated, NOT the new update from C1
//         printUserData("Reputation 2 Result (should be old data)", data4);

//         vm.stopBroadcast();
//     }

//     /**
//      * @dev Helper function to print UserData struct details, like decode.sh.
//      */
//     function printUserData(string memory label, Reputation.UserData memory data) internal {
//         console.log("--- Decoded UserData: %s ---", label);
//         if (data.passwordHash == bytes32(0)) {
//             console.log("  (User not found or empty data)");
//             return;
//         }
//         console.log("  Username:      '%s'", data.username);
//         console.log("  Salt:          '%s'", data.salt);
//         console.log("  Download:      %s", data.downloadSize);
//         console.log("  Upload:        %s", data.uploadSize);
//         console.log("  Password Hash: %s", vm.toString(data.passwordHash));
//         console.log("------------------------------------");
//     }
// }
