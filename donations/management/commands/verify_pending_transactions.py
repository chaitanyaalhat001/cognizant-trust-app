from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from donations.models import DonationTransaction
from web3 import Web3
import urllib3
import logging

# Disable SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verify pending blockchain transactions and update their status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Check transactions from the last N hours (default: 24)'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find donations that might have pending blockchain transactions
        pending_donations = DonationTransaction.objects.filter(
            blockchain_status='pending',
            created_at__gte=cutoff_time
        )
        
        self.stdout.write(f"🔍 Checking {pending_donations.count()} pending donations from last {hours} hours...")
        
        # Initialize Web3 connection
        providers = [
            'https://sepolia.infura.io/v3/15c1ff74c2d04f928cda7bcc7167207b',
            'https://ethereum-sepolia-rpc.publicnode.com',
            'https://sepolia.drpc.org',
            'https://rpc.sepolia.org'
        ]
        
        w3 = None
        for provider_url in providers:
            try:
                request_kwargs = {'timeout': 15, 'verify': False}
                test_w3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs=request_kwargs))
                if test_w3.eth.chain_id == 11155111:  # Sepolia
                    w3 = test_w3
                    self.stdout.write(f"✅ Connected to Sepolia via {provider_url}")
                    break
            except Exception as e:
                self.stdout.write(f"⚠️ Failed to connect to {provider_url}: {e}")
        
        if not w3:
            self.stdout.write(self.style.ERROR("❌ Could not connect to any Sepolia provider"))
            return
        
        updated_count = 0
        
        for donation in pending_donations:
            if donation.attempted_tx_hash:
                try:
                    self.stdout.write(f"🔍 Checking {donation.donor_name}: {donation.attempted_tx_hash}")
                    
                    # Get transaction receipt
                    receipt = w3.eth.get_transaction_receipt(donation.attempted_tx_hash)
                    
                    if receipt and receipt['status'] == 1:
                        # Transaction succeeded - update status
                        donation.blockchain_status = 'recorded'
                        donation.blockchain_tx_hash = donation.attempted_tx_hash
                        donation.save()
                        updated_count += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Updated {donation.donor_name}: Transaction successful!"
                            )
                        )
                    elif receipt and receipt['status'] == 0:
                        # Transaction failed - keep as pending for retry
                        self.stdout.write(
                            self.style.WARNING(
                                f"❌ {donation.donor_name}: Transaction failed on blockchain, keeping as pending for retry"
                            )
                        )
                        # Don't change status - keep as 'pending' so it can be retried
                    else:
                        self.stdout.write(f"⏳ {donation.donor_name}: Transaction still pending")
                        
                except Exception as e:
                    self.stdout.write(f"⚠️ Error checking {donation.attempted_tx_hash}: {e}")
            else:
                self.stdout.write(f"📝 {donation.donor_name}: No attempted transaction hash to check")
        
        self.stdout.write(f"✅ Verification complete. Updated {updated_count} donations.") 