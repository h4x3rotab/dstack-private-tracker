// SPDX-License-Identifier: MIT
pragma solidity ^0.8.12;

/**
 * @title Reputation
 * @dev This contract holds data for MULTIPLE users in a mapping.
 * It implements a "chained-lookup" to a referrer contract for data continuity.
 * Data is publicly readable, but only the owner (the TEE) can write to this contract.
 */
contract Reputation {
    /**
     * @dev Data structure to hold user information.
     */
    struct UserData {
        string username;
        string salt;
        bytes32 passwordHash;
        uint256 downloadSize;
        uint256 uploadSize;
    }

    // The address of the entity (TEE) that owns this contract and can modify its data.
    address public owner;

    // The address of the previous contract to refer to for data lookups.
    address public referrerReputation;

    // Mapping to store the data for all users in THIS contract instance.
    mapping(string => UserData) public allUsers;

    /**
     * @dev The constructor is called by the ReputationFactory.
     * @param _creator The TEE address that will own this new Reputation.
     * @param _referrerReputation The address of the old contract to chain lookups to.
     */
    constructor(address _creator, address _referrerReputation) {
        owner = _creator;
        
        // Only set referrer if it's not zero address AND has contract code
        if (_referrerReputation != address(0) && _referrerReputation.code.length > 0) {
            // Additional check: ensure it's actually a Reputation contract
            try Reputation(_referrerReputation).owner() returns (address) {
                referrerReputation = _referrerReputation;
            } catch {
                // If the contract doesn't have the expected interface, don't set it
                // referrerReputation remains address(0)
            }
        }
        // If no valid referrer, referrerReputation remains address(0) (default)
    }

    /**
     * @dev Modifier to ensure only the owner of this contract can call a function.
     */
    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can call this function.");
        _;
    }
    
    /**
     * @dev Custom getter to perform a single-level lookup for user data.
     * It first checks this contract, then falls back to the immediate referrer.
     * If data is found in referrer, it copies it to this contract for future lookups.
     * @param _username The username to look up.
     * @return _ The UserData struct for the user.
     */
    function retrieveUserData(string memory _username) public returns (UserData memory) {
        // Check for existence by looking at a field that should not be empty for a real user.
        if (allUsers[_username].passwordHash != bytes32(0)) {
            // If user data exists in this (the newest) contract, return it.
            return allUsers[_username];
        } else if (referrerReputation != address(0)) {
            // If not found here, check the immediate referrer's data
            try Reputation(referrerReputation).getUserData(_username) returns (UserData memory referrerData) {
                if (referrerData.passwordHash != bytes32(0)) {
                    // Data found in referrer! Copy it to current contract for future lookups
                    allUsers[_username] = UserData({
                        username: referrerData.username,
                        salt: referrerData.salt,
                        passwordHash: referrerData.passwordHash,
                        downloadSize: referrerData.downloadSize,
                        uploadSize: referrerData.uploadSize
                    });
                    
                    // Return the data
                    return referrerData;
                }
            } catch {
                // Handle the case where the external call fails
                // Fall through to return empty struct
            }
        }
        
        // If not found in current contract or immediate referrer, return empty struct
        return UserData("", "", bytes32(0), 0, 0);
    }

    /**
     * @dev Adds a new user's data IN THIS CONTRACT.
     * This is the function your TEE calls to migrate data or create it.
     * It can only be called by the contract owner.
     * @param _username The username that acts as the key in the mapping.
     * @param _salt The user's salt.
     * @param _passwordHash The user's password hash.
     * @param _downloadSize The user's total download size.
     * @param _uploadSize The user's total upload size.
     */
    function addUser(
        string memory _username,
        string memory _salt,
        bytes32 _passwordHash,
        uint256 _downloadSize,
        uint256 _uploadSize
    ) public onlyOwner {
        // This function writes the data to this contract's local storage.
        allUsers[_username] = UserData({
            username: _username,
            salt: _salt,
            passwordHash: _passwordHash,
            downloadSize: _downloadSize,
            uploadSize: _uploadSize
        });
    }
        /**
     * @dev Updates an existing user's data IN THIS CONTRACT.
     * This is the function your TEE calls to migrate data or update it.
     * It can only be called by the contract owner.
     * @param _username The username that acts as the key in the mapping.
     * @param _downloadSize The user's total download size.
     * @param _uploadSize The user's total upload size.
     */
    function updateUser(
        string memory _username,
        uint256 _downloadSize,
        uint256 _uploadSize
    ) public onlyOwner {
        require(allUsers[_username].passwordHash != bytes32(0), "User does not exist");
        allUsers[_username].downloadSize = _downloadSize;
        allUsers[_username].uploadSize = _uploadSize;
    }
}
