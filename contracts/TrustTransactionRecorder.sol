// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract TrustTransactionRecorder {
    struct Transaction {
        string donorName;
        uint256 amount;
        string purpose;
        string upiRefId;
        address adminWallet;
        uint256 timestamp;
        bytes32 transactionHash;
    }
    
    mapping(bytes32 => Transaction) public transactions;
    bytes32[] public transactionHashes;
    
    event TransactionRecorded(
        bytes32 indexed transactionHash,
        string donorName,
        uint256 amount,
        string purpose,
        string upiRefId,
        address indexed adminWallet,
        uint256 timestamp
    );
    
    modifier onlyAdmin() {
        require(msg.sender != address(0), "Invalid admin address");
        _;
    }
    
    function recordTransaction(
        string memory donorName,
        uint256 amount,
        string memory purpose,
        string memory upiRefId,
        address adminWallet
    ) public onlyAdmin returns (bytes32) {
        require(bytes(donorName).length > 0, "Donor name cannot be empty");
        require(amount > 0, "Amount must be greater than 0");
        require(bytes(purpose).length > 0, "Purpose cannot be empty");
        require(bytes(upiRefId).length > 0, "UPI reference ID cannot be empty");
        require(adminWallet != address(0), "Invalid admin wallet address");
        
        bytes32 txHash = keccak256(
            abi.encodePacked(
                donorName,
                amount,
                purpose,
                upiRefId,
                adminWallet,
                block.timestamp,
                block.number
            )
        );
        
        require(transactions[txHash].timestamp == 0, "Transaction already recorded");
        
        Transaction memory newTransaction = Transaction({
            donorName: donorName,
            amount: amount,
            purpose: purpose,
            upiRefId: upiRefId,
            adminWallet: adminWallet,
            timestamp: block.timestamp,
            transactionHash: txHash
        });
        
        transactions[txHash] = newTransaction;
        transactionHashes.push(txHash);
        
        emit TransactionRecorded(
            txHash,
            donorName,
            amount,
            purpose,
            upiRefId,
            adminWallet,
            block.timestamp
        );
        
        return txHash;
    }
    
    function getTransaction(bytes32 txHash) public view returns (
        string memory donorName,
        uint256 amount,
        string memory purpose,
        string memory upiRefId,
        address adminWallet,
        uint256 timestamp
    ) {
        Transaction memory txn = transactions[txHash];
        require(txn.timestamp != 0, "Transaction not found");
        
        return (
            txn.donorName,
            txn.amount,
            txn.purpose,
            txn.upiRefId,
            txn.adminWallet,
            txn.timestamp
        );
    }
    
    function getTotalTransactions() public view returns (uint256) {
        return transactionHashes.length;
    }
    
    function getTransactionByIndex(uint256 index) public view returns (bytes32) {
        require(index < transactionHashes.length, "Index out of bounds");
        return transactionHashes[index];
    }
} 