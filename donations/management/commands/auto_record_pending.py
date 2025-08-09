from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from donations.models import DonationTransaction, AutoRecordingSettings
from web3_integration.auto_recorder import auto_recorder
from cognizanttrust.crypto_utils import credential_manager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scan database for pending transactions and automatically record them on blockchain'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Scan transactions from the last N hours (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be recorded without actually doing it'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No actual blockchain transactions will be sent"))
        
        # Check if auto-recording is enabled
        try:
            settings = AutoRecordingSettings.get_settings()
            if not settings.is_automatic_mode:
                self.stdout.write(self.style.ERROR("❌ Auto-recording is disabled. Please enable it first."))
                return
            
            if not settings.credentials_configured:
                self.stdout.write(self.style.ERROR("❌ No credentials configured for auto-recording."))
                return
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error checking settings: {e}"))
            return
        
        # Check if credentials exist
        if not credential_manager.credentials_exist():
            self.stdout.write(self.style.ERROR("❌ No encrypted credentials found."))
            return
        
        # Initialize auto-recorder if not already done
        if not auto_recorder.is_initialized:
            if not auto_recorder.auto_initialize():
                self.stdout.write(self.style.ERROR("❌ Could not initialize auto-recorder. Please toggle auto-mode in admin panel."))
                return
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find pending donations that haven't been recorded
        pending_donations = DonationTransaction.objects.filter(
            blockchain_status='pending',
            created_at__gte=cutoff_time
        ).order_by('created_at')
        
        self.stdout.write(f"🔍 Found {pending_donations.count()} pending donations from last {hours} hours...")
        
        if not pending_donations.exists():
            self.stdout.write(self.style.SUCCESS("✅ No pending donations found. All caught up!"))
            return
        
        recorded_count = 0
        failed_count = 0
        
        for donation in pending_donations:
            try:
                self.stdout.write(f"📝 Processing: {donation.donor_name} - ₹{donation.amount} - {donation.purpose}")
                
                if dry_run:
                    self.stdout.write(f"   🧪 Would record on blockchain: {donation.id}")
                    continue
                
                # Attempt automatic blockchain recording
                result = auto_recorder.record_donation_automatically(
                    donor_name=donation.donor_name,
                    amount=float(donation.amount),
                    purpose=donation.purpose,
                    upi_ref_id=donation.upi_ref_id
                )
                
                if result.get('success'):
                    # Update donation with blockchain info
                    donation.attempted_tx_hash = result.get('tx_hash')
                    
                    # Check if we got immediate confirmation or timeout
                    tx_note = result.get('note', '')
                    if tx_note:
                        # Receipt timed out - keep as pending but with attempted hash
                        donation.blockchain_status = 'pending'
                        self.stdout.write(
                            self.style.WARNING(
                                f"   ⏳ Sent to blockchain (pending confirmation): {result.get('tx_hash')}"
                            )
                        )
                    else:
                        # Receipt received successfully
                        donation.blockchain_status = 'recorded'
                        donation.blockchain_tx_hash = result.get('tx_hash')
                        recorded_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"   ✅ Successfully recorded: {result.get('tx_hash')}"
                            )
                        )
                    
                    # Update admin wallet and save
                    donation.admin_wallet = auto_recorder.account.address if auto_recorder.account else None
                    donation.save()
                    
                else:
                    failed_count += 1
                    error_msg = result.get('error', 'Unknown error')
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Failed to record: {error_msg}")
                    )
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Exception while processing {donation.donor_name}: {e}")
                )
                logger.error(f"Error auto-recording donation {donation.id}: {e}")
        
        if dry_run:
            self.stdout.write(f"🧪 DRY RUN COMPLETE: Would have processed {pending_donations.count()} donations")
        else:
            self.stdout.write(f"✅ SCAN COMPLETE:")
            self.stdout.write(f"   📊 Total processed: {pending_donations.count()}")
            self.stdout.write(f"   ✅ Successfully recorded: {recorded_count}")
            self.stdout.write(f"   ⏳ Sent (pending confirmation): {pending_donations.count() - recorded_count - failed_count}")
            self.stdout.write(f"   ❌ Failed: {failed_count}") 