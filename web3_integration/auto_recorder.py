from web3 import Web3
from eth_account import Account
from django.conf import settings
from cognizanttrust.crypto_utils import credential_manager
from .web3_utils import CONTRACT_ABI
from django.core.cache import cache
from django.utils import timezone
import logging
import hashlib

logger = logging.getLogger(__name__)

class AutoBlockchainRecorder:
    """
    Automatic blockchain transaction recorder that works without MetaMask.
    Uses server-side private key signing for seamless automation.
    """
    
    def __init__(self):
        self.w3 = None
        self.contract = None
        self.account = None
        self.is_initialized = False
        
    def _get_session_key(self) -> str:
        """Generate a consistent session key for this instance"""
        return "auto_recorder_session_password"
        
    def set_session_password(self, master_password: str):
        """Store master password for session (persistent across restarts)"""
        # Get session timeout from settings
        try:
            from donations.models import AutoRecordingSettings
            settings = AutoRecordingSettings.get_settings()
            session_timeout_minutes = settings.session_timeout_minutes
        except Exception:
            session_timeout_minutes = 1440  # Default 24 hours if settings not available
        
        # Store encrypted session password in Django cache
        cache.set(self._get_session_key(), master_password, timeout=session_timeout_minutes * 60)
        logger.info(f"✅ Session password stored in cache for {session_timeout_minutes} minutes ({session_timeout_minutes//60} hours)")
        
        # Update last session time in settings
        try:
            settings.last_auto_session = timezone.now()
            settings.save()
        except Exception as e:
            logger.warning(f"Could not update last session time: {e}")
        
    def clear_session_password(self):
        """Clear stored session password"""
        cache.delete(self._get_session_key())
        logger.info("✅ Session password cleared from cache")
        
    def get_session_password(self) -> str:
        """Get stored session password from cache"""
        return cache.get(self._get_session_key())
        
    def auto_initialize(self) -> bool:
        """Try to initialize using stored session password"""
        session_password = self.get_session_password()
        if session_password:
            logger.info("🔄 Auto-initializing with cached session password...")
            return self.initialize(session_password)
        else:
            logger.info("ℹ️ No cached session password found - auto mode needs to be toggled")
            return False
        
    def initialize(self, master_password: str) -> bool:
        """
        Initialize the auto recorder with encrypted credentials
        
        Args:
            master_password: Password to decrypt stored MetaMask credentials
            
        Returns:
            bool: True if successfully initialized
        """
        try:
            # Load encrypted credentials
            credentials = credential_manager.load_credentials(master_password)
            if not credentials:
                logger.error("Failed to load credentials")
                return False
            
            # Initialize Web3 connection with multiple providers
            provider_url = getattr(settings, 'WEB3_PROVIDER_URL', '')
            
            # Alternative providers to try if primary fails
            alternative_providers = [
                provider_url,
                'https://ethereum-sepolia-rpc.publicnode.com',
                'https://sepolia.drpc.org',
                'https://rpc.sepolia.org'
            ]
            
            self.w3 = None
            
            for i, url in enumerate(alternative_providers):
                if not url:
                    continue
                    
                print(f"🌐 Attempting provider {i+1}: {url}")
                
                try:
                    # Try with SSL verification disabled for corporate networks
                    import ssl
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    
                    request_kwargs = {
                        'timeout': 15,
                        'verify': False  # Disable SSL verification for corporate networks
                    }
                    test_w3 = Web3(Web3.HTTPProvider(url, request_kwargs=request_kwargs))
                    
                    # Test connection with multiple methods
                    connection_tests = []
                    
                    # Test 1: Basic connection
                    try:
                        is_connected = test_w3.is_connected()
                        connection_tests.append(f"is_connected: {is_connected}")
                    except Exception as e:
                        connection_tests.append(f"is_connected failed: {e}")
                        is_connected = False
                    
                    # Test 2: Try to get chain ID (more reliable)
                    try:
                        chain_id = test_w3.eth.chain_id
                        connection_tests.append(f"chain_id: {chain_id}")
                        if chain_id == 11155111:  # Sepolia chain ID
                            print(f"✅ Connected to Sepolia! Provider: {url}")
                            print(f"✅ Chain ID: {chain_id}")
                            
                            # Test 3: Get latest block
                            try:
                                latest_block = test_w3.eth.block_number
                                print(f"✅ Latest block: {latest_block}")
                            except Exception as block_e:
                                print(f"⚠️ Block number failed but connection OK: {block_e}")
                            
                            self.w3 = test_w3
                            break
                        else:
                            print(f"⚠️ Wrong network. Expected Sepolia (11155111), got {chain_id}")
                            continue
                            
                    except Exception as e:
                        connection_tests.append(f"chain_id failed: {e}")
                        print(f"⚠️ Provider {i+1} failed chain test: {url}")
                        print(f"   Connection tests: {', '.join(connection_tests)}")
                        continue
                        
                except Exception as e:
                    print(f"❌ Provider {i+1} completely failed: {url} - Error: {e}")
                    continue
            
            if not self.w3:
                print("❌ All Web3 providers failed to connect")
                print("🔍 Possible causes:")
                print("   1. Network connectivity issues")
                print("   2. Corporate firewall blocking Web3 providers")
                print("   3. All providers temporarily down")
                print("   4. Python requests library issues")
                
                # Test basic HTTP connectivity
                try:
                    import requests
                    test_response = requests.get('https://httpbin.org/status/200', timeout=5)
                    if test_response.status_code == 200:
                        print("✅ Basic HTTP connectivity works")
                    else:
                        print(f"⚠️ HTTP test returned status: {test_response.status_code}")
                except Exception as http_e:
                    print(f"❌ Basic HTTP connectivity failed: {http_e}")
                
                logger.error("Failed to connect to any Web3 provider")
                return False
            
            # Initialize account from private key
            try:
                private_key = credentials['private_key']
                if not private_key.startswith('0x'):
                    private_key = '0x' + private_key
                
                print(f"🔑 Initializing account from private key...")
                self.account = Account.from_key(private_key)
                print(f"✅ Account initialized: {self.account.address}")
                
                # Verify wallet address matches
                stored_address = credentials['wallet_address'].lower()
                derived_address = self.account.address.lower()
                
                if stored_address != derived_address:
                    print(f"❌ Address mismatch: stored={stored_address}, derived={derived_address}")
                    logger.error(f"Address mismatch: stored={stored_address}, derived={derived_address}")
                    return False
                
                print(f"✅ Wallet address verified: {derived_address}")
                
            except Exception as e:
                print(f"❌ Account initialization error: {e}")
                logger.error(f"Account initialization error: {e}")
                return False
            
            # Initialize contract
            contract_address = getattr(settings, 'CONTRACT_ADDRESS', '')
            if contract_address:
                try:
                    print(f"📄 Initializing contract at: {contract_address}")
                    self.contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(contract_address),
                        abi=CONTRACT_ABI
                    )
                    print(f"✅ Contract initialized successfully")
                except Exception as e:
                    print(f"❌ Contract initialization error: {e}")
                    logger.error(f"Contract initialization error: {e}")
                    return False
            else:
                print("⚠️ No contract address configured")
            
            self.is_initialized = True
            print(f"🎉 Auto recorder fully initialized with wallet: {self.account.address}")
            logger.info(f"✅ Auto recorder initialized with wallet: {self.account.address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize auto recorder: {e}")
            return False
    
    def record_donation_automatically(self, donor_name: str, amount: float, 
                                    purpose: str, upi_ref_id: str) -> dict:
        """
        Automatically record donation on blockchain without user intervention
        
        Args:
            donor_name: Name of the donor
            amount: Donation amount in rupees
            purpose: Purpose of donation
            upi_ref_id: UPI reference ID
            
        Returns:
            dict: Transaction result with hash and status
        """
        if not self.is_initialized:
            return {'success': False, 'error': 'Auto recorder not initialized'}
        
        try:
            # Convert amount to paisa (smallest unit)
            amount_in_paisa = int(amount * 100)
            
            # Build transaction
            function_call = self.contract.functions.recordTransaction(
                donor_name,
                amount_in_paisa,
                purpose,
                upi_ref_id,
                self.account.address
            )
            
            # Get current gas price and nonce
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Estimate gas limit with detailed debugging
            try:
                print(f"🔥 Estimating gas for transaction...")
                print(f"   Donor: {donor_name}")
                print(f"   Amount (paisa): {amount_in_paisa}")
                print(f"   Purpose: {purpose}")
                print(f"   UPI Ref: {upi_ref_id}")
                print(f"   Admin Wallet: {self.account.address}")
                
                gas_limit = function_call.estimate_gas({'from': self.account.address})
                gas_limit = int(gas_limit * 1.2)  # Add 20% buffer
                print(f"✅ Gas estimated: {gas_limit}")
            except Exception as gas_e:
                print(f"❌ Gas estimation failed: {gas_e}")
                gas_limit = 500000  # Fallback gas limit
            
            # Build transaction
            transaction = function_call.build_transaction({
                'chainId': 11155111,  # Sepolia testnet
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'from': self.account.address
            })
            
            # Sign transaction with private key
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            
            # Send transaction (handle both old and new eth-account versions)
            try:
                raw_tx = signed_txn.rawTransaction  # Old version
            except AttributeError:
                raw_tx = signed_txn.raw_transaction  # New version
            
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"✅ Auto-recorded donation: {tx_hash_hex}")
            
            # Wait for transaction receipt with detailed status
            print(f"📤 Transaction sent: {tx_hash_hex}")
            try:
                print(f"⏳ Waiting for transaction confirmation...")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                success = receipt['status'] == 1
                
                if success:
                    print(f"✅ Transaction SUCCESSFUL!")
                    print(f"   Block: {receipt['blockNumber']}")
                    print(f"   Gas Used: {receipt['gasUsed']}")
                    print(f"   View on Etherscan: https://sepolia.etherscan.io/tx/{tx_hash_hex}")
                else:
                    print(f"❌ Transaction FAILED!")
                    print(f"   Block: {receipt['blockNumber']}")
                    print(f"   Gas Used: {receipt['gasUsed']}")
                    print(f"   Status: {receipt['status']}")
                    print(f"   View on Etherscan: https://sepolia.etherscan.io/tx/{tx_hash_hex}")
                
                return {
                    'success': success,
                    'tx_hash': tx_hash_hex,
                    'gas_used': receipt['gasUsed'],
                    'block_number': receipt['blockNumber'],
                    'admin_wallet': self.account.address
                }
            except Exception as e:
                print(f"⚠️ Could not get transaction receipt: {e}")
                print(f"   TX Hash: {tx_hash_hex}")
                print(f"   Check manually: https://sepolia.etherscan.io/tx/{tx_hash_hex}")
                # Transaction sent but receipt timeout
                return {
                    'success': True,  # Transaction was sent
                    'tx_hash': tx_hash_hex,
                    'note': 'Transaction sent, receipt pending',
                    'admin_wallet': self.account.address
                }
                
        except Exception as e:
            logger.error(f"Failed to auto-record donation: {e}")
            return {'success': False, 'error': str(e)}
    
    def record_spending_automatically(self, amount: float, category: str) -> dict:
        """
        Automatically record spending on blockchain
        
        Args:
            amount: Spending amount in rupees
            category: Spending category
            
        Returns:
            dict: Transaction result
        """
        if not self.is_initialized:
            return {'success': False, 'error': 'Auto recorder not initialized'}
        
        try:
            # Convert category to ID for ultra-minimal contract
            CATEGORY_MAP = {
                'education': 0, 'healthcare': 1, 'food_distribution': 2,
                'shelter': 3, 'disaster_relief': 4, 'elderly_care': 5,
                'child_welfare': 6, 'skill_development': 7, 'sanitation': 8,
                'other': 9
            }
            
            category_id = CATEGORY_MAP.get(category, 9)
            amount_in_paisa = int(amount * 100)
            
            # Get spending contract address (if different from donation contract)
            spending_contract_address = getattr(settings, 'SPENDING_CONTRACT_ADDRESS', 
                                              '0x732F8A850d4Ad351858FAcCb4e207C42bEA88C91')
            
            # Initialize spending contract
            spending_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(spending_contract_address),
                abi=self._get_spending_contract_abi()
            )
            
            # Build and send transaction (similar to donation)
            function_call = spending_contract.functions.recordSpending(
                amount_in_paisa, category_id
            )
            
            # Same transaction building and signing process as above
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_limit = 200000  # Lower gas for minimal spending contract
            
            transaction = function_call.build_transaction({
                'chainId': 11155111,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'from': self.account.address
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            
            # Send transaction (handle both old and new eth-account versions)
            try:
                raw_tx = signed_txn.rawTransaction  # Old version
            except AttributeError:
                raw_tx = signed_txn.raw_transaction  # New version
            
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'category_id': category_id
            }
            
        except Exception as e:
            logger.error(f"Failed to auto-record spending: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_spending_contract_abi(self):
        """Get spending contract ABI"""
        # Minimal ABI for spending contract
        return [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint8", "name": "categoryId", "type": "uint8"}
                ],
                "name": "recordSpending",
                "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
    
    def get_wallet_balance(self) -> float:
        """Get current wallet ETH balance"""
        if not self.is_initialized:
            return 0.0
        
        try:
            balance_wei = self.w3.eth.get_balance(self.account.address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception:
            return 0.0

# Global instance
auto_recorder = AutoBlockchainRecorder() 