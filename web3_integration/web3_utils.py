from web3 import Web3
from django.conf import settings
import json

# Contract ABI (Application Binary Interface)
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "donorName", "type": "string"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "string", "name": "purpose", "type": "string"},
            {"internalType": "string", "name": "upiRefId", "type": "string"},
            {"internalType": "address", "name": "adminWallet", "type": "address"}
        ],
        "name": "recordTransaction",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "txHash", "type": "bytes32"}],
        "name": "getTransaction",
        "outputs": [
            {"internalType": "string", "name": "donorName", "type": "string"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "string", "name": "purpose", "type": "string"},
            {"internalType": "string", "name": "upiRefId", "type": "string"},
            {"internalType": "address", "name": "adminWallet", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalTransactions",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "transactionHash", "type": "bytes32"},
            {"indexed": False, "internalType": "string", "name": "donorName", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "purpose", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "upiRefId", "type": "string"},
            {"indexed": True, "internalType": "address", "name": "adminWallet", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "TransactionRecorded",
        "type": "event"
    }
]

class Web3Manager:
    def __init__(self):
        self.w3 = None
        self.contract = None
        self.contract_address = getattr(settings, 'CONTRACT_ADDRESS', '')
        
    def init_web3(self, provider_url=None):
        """Initialize Web3 connection"""
        if not provider_url:
            provider_url = getattr(settings, 'WEB3_PROVIDER_URL', '')
        
        if provider_url:
            self.w3 = Web3(Web3.HTTPProvider(provider_url))
            return self.w3.is_connected()
        return False
    
    def init_contract(self, contract_address=None):
        """Initialize contract instance"""
        if not self.w3:
            return False
            
        address = contract_address or self.contract_address
        if address:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(address),
                abi=CONTRACT_ABI
            )
            return True
        return False
    
    def get_contract_abi(self):
        """Get contract ABI for frontend"""
        return CONTRACT_ABI
    
    def validate_transaction_data(self, donor_name, amount, purpose, upi_ref_id, admin_wallet):
        """Validate transaction data before sending to blockchain"""
        errors = []
        
        if not donor_name or not donor_name.strip():
            errors.append("Donor name is required")
        
        if not amount or amount <= 0:
            errors.append("Amount must be greater than 0")
            
        if not purpose or not purpose.strip():
            errors.append("Purpose is required")
            
        if not upi_ref_id or not upi_ref_id.strip():
            errors.append("UPI Reference ID is required")
            
        if not admin_wallet:
            errors.append("Admin wallet address is required")
        elif not Web3.is_address(admin_wallet):
            errors.append("Invalid admin wallet address")
            
        return errors
    
    def encode_transaction_data(self, donor_name, amount, purpose, upi_ref_id, admin_wallet):
        """Encode transaction data for frontend use"""
        if not self.contract:
            return None
            
        try:
            # Convert amount to wei (assuming input is in rupees, convert to smallest unit)
            amount_wei = int(amount * 100)  # Convert to paisa equivalent
            
            function_data = self.contract.encodeABI(
                fn_name='recordTransaction',
                args=[
                    donor_name,
                    amount_wei,
                    purpose,
                    upi_ref_id,
                    Web3.to_checksum_address(admin_wallet)
                ]
            )
            
            return {
                'to': self.contract_address,
                'data': function_data,
                'gas': 500000,  # Estimated gas limit
            }
        except Exception as e:
            print(f"Error encoding transaction data: {e}")
            return None

# Initialize global web3 manager
web3_manager = Web3Manager() 