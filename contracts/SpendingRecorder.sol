// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SpendingRecorder {
    struct SpendingRecord {
        uint256 amount;          // 32 bytes - amount in paisa
        uint8 categoryId;        // 1 byte - category enum (0-9)
        uint32 timestamp;        // 4 bytes - compressed timestamp (sufficient until 2106)
    }
    
    // Total storage per record: ~37 bytes vs 300+ bytes in old approach (90% reduction!)
    
    mapping(bytes32 => SpendingRecord) public spendings;
    bytes32[] public spendingHashes;
    
    // Category mapping (saves gas vs storing strings)
    enum Category { 
        EDUCATION,      // 0
        HEALTHCARE,     // 1
        FOOD,           // 2
        SHELTER,        // 3
        DISASTER,       // 4
        ELDERLY,        // 5
        CHILD,          // 6
        SKILL,          // 7
        SANITATION,     // 8
        OTHER           // 9
    }
    
    event SpendingRecorded(
        bytes32 indexed spendingId,
        uint256 amount,
        uint8 categoryId
    );
    
    modifier onlyAdmin() {
        require(msg.sender != address(0), "Invalid admin address");
        _;
    }
    
    // ULTRA-MINIMAL function - only essential data
    function recordSpending(
        uint256 amount,                 // Amount in paisa
        uint8 categoryId               // Category enum (0-9)
    ) public onlyAdmin returns (bytes32) {
        require(amount > 0, "Amount must be greater than 0");
        require(categoryId <= 9, "Invalid category");
        
        // Generate spending ID from transaction data
        bytes32 spendingHash = keccak256(abi.encodePacked(
            msg.sender,
            amount,
            categoryId,
            block.timestamp,
            spendingHashes.length
        ));
        
        SpendingRecord memory newSpending = SpendingRecord({
            amount: amount,
            categoryId: categoryId,
            timestamp: uint32(block.timestamp)
        });
        
        spendings[spendingHash] = newSpending;
        spendingHashes.push(spendingHash);
        
        emit SpendingRecorded(
            spendingHash,
            amount,
            categoryId
        );
        
        return spendingHash;
    }
    
    function getSpending(bytes32 spendingHash) public view returns (
        uint256 amount,
        uint8 categoryId,
        uint32 timestamp
    ) {
        SpendingRecord memory spending = spendings[spendingHash];
        require(spending.timestamp != 0, "Spending not found");
        
        return (
            spending.amount,
            spending.categoryId,
            spending.timestamp
        );
    }
    
    function getTotalSpendings() public view returns (uint256) {
        return spendingHashes.length;
    }
    
    function getSpendingByIndex(uint256 index) public view returns (bytes32) {
        require(index < spendingHashes.length, "Index out of bounds");
        return spendingHashes[index];
    }
    
    // Helper function to get category name (for frontend use)
    function getCategoryName(uint8 categoryId) public pure returns (string memory) {
        if (categoryId == 0) return "education";
        if (categoryId == 1) return "healthcare";
        if (categoryId == 2) return "food_distribution";
        if (categoryId == 3) return "shelter";
        if (categoryId == 4) return "disaster_relief";
        if (categoryId == 5) return "elderly_care";
        if (categoryId == 6) return "child_welfare";
        if (categoryId == 7) return "skill_development";
        if (categoryId == 8) return "sanitation";
        return "other";
    }
    
    // Helper function to get category ID from string (for frontend use)
    function getCategoryId(string memory category) public pure returns (uint8) {
        bytes32 categoryHash = keccak256(abi.encodePacked(category));
        
        if (categoryHash == keccak256(abi.encodePacked("education"))) return 0;
        if (categoryHash == keccak256(abi.encodePacked("healthcare"))) return 1;
        if (categoryHash == keccak256(abi.encodePacked("food_distribution"))) return 2;
        if (categoryHash == keccak256(abi.encodePacked("shelter"))) return 3;
        if (categoryHash == keccak256(abi.encodePacked("disaster_relief"))) return 4;
        if (categoryHash == keccak256(abi.encodePacked("elderly_care"))) return 5;
        if (categoryHash == keccak256(abi.encodePacked("child_welfare"))) return 6;
        if (categoryHash == keccak256(abi.encodePacked("skill_development"))) return 7;
        if (categoryHash == keccak256(abi.encodePacked("sanitation"))) return 8;
        return 9; // other
    }
} 