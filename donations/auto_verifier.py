"""
Auto-verifier for pending blockchain transactions
Automatically checks and updates transactions that have timed out
"""

import logging
import time
import threading
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from .models import DonationTransaction
from web3 import Web3
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class AutoVerifier:
    """Automatically verify pending transactions in the background"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.w3 = None
        self._initialize_web3()
    
    def _initialize_web3(self):
        """Initialize Web3 connection"""
        providers = [
            'https://sepolia.infura.io/v3/15c1ff74c2d04f928cda7bcc7167207b',
            'https://ethereum-sepolia-rpc.publicnode.com',
            'https://sepolia.drpc.org',
            'https://rpc.sepolia.org'
        ]
        
        for provider_url in providers:
            try:
                request_kwargs = {'timeout': 15, 'verify': False}
                test_w3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs=request_kwargs))
                if test_w3.eth.chain_id == 11155111:  # Sepolia
                    self.w3 = test_w3
                    logger.info(f"✅ Auto-verifier connected to Sepolia via {provider_url}")
                    break
            except Exception as e:
                logger.warning(f"Failed to connect to {provider_url}: {e}")
                continue
    
    def verify_pending_transactions(self):
        """Verify all pending transactions with attempted_tx_hash"""
        if not self.w3:
            logger.error("❌ No Web3 connection available for verification")
            return {'updated_count': 0, 'error': 'No blockchain connection'}
        
        try:
            # Find ALL donations with attempted_tx_hash but still pending
            # Scan entire database - no time limit
            pending_donations = DonationTransaction.objects.filter(
                blockchain_status='pending',
                attempted_tx_hash__isnull=False
            ).exclude(attempted_tx_hash='')
            
            updated_count = 0
            
            for donation in pending_donations:
                try:
                    # Get transaction receipt
                    receipt = self.w3.eth.get_transaction_receipt(donation.attempted_tx_hash)
                    
                    if receipt and receipt['status'] == 1:
                        # Transaction succeeded - update to recorded
                        with transaction.atomic():
                            donation.blockchain_status = 'recorded'
                            donation.blockchain_tx_hash = donation.attempted_tx_hash
                            donation.save()
                            updated_count += 1
                            
                        logger.info(f"✅ Auto-verified successful: {donation.donor_name} -> {donation.attempted_tx_hash}")
                        
                    elif receipt and receipt['status'] == 0:
                        # Transaction failed - clear attempted_tx_hash so it can be retried by Thread 2
                        with transaction.atomic():
                            donation.attempted_tx_hash = None  # Clear the failed tx hash
                            donation.save()
                            updated_count += 1
                            
                        logger.warning(f"❌ Transaction failed, cleared tx_hash for retry: {donation.donor_name} -> {donation.attempted_tx_hash}")
                        # Status stays 'pending' and Thread 2 can now retry it
                        
                except Exception as e:
                    logger.debug(f"Could not verify {donation.attempted_tx_hash}: {e}")
                    # Transaction might still be pending, skip for now
                    continue
            
            return {'updated_count': updated_count, 'success': True}
            
        except Exception as e:
            logger.error(f"Error in auto-verification: {e}")
            return {'updated_count': 0, 'error': str(e)}
    
    def start_background_verification(self, interval_seconds=300):
        """Start background verification every 5 minutes"""
        if self.running:
            logger.warning("Auto-verifier already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._verification_loop, args=(interval_seconds,))
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"🚀 Auto-verifier started (checking every {interval_seconds} seconds)")
    
    def stop_background_verification(self):
        """Stop background verification"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("⏹️ Auto-verifier stopped")
    
    def _verification_loop(self, interval_seconds):
        """Background loop for verification"""
        while self.running:
            try:
                result = self.verify_pending_transactions()
                if result.get('updated_count', 0) > 0:
                    logger.info(f"🔄 Auto-verified {result['updated_count']} transactions")
            except Exception as e:
                logger.error(f"Error in verification loop: {e}")
            
            # Sleep with interruption check
            for _ in range(interval_seconds):
                if not self.running:
                    break
                time.sleep(1)

# Global auto-verifier instance
auto_verifier = AutoVerifier()

def start_auto_verifier():
    """Start the auto-verifier if not already running"""
    auto_verifier.start_background_verification()

def stop_auto_verifier():
    """Stop the auto-verifier"""
    auto_verifier.stop_background_verification() 