from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from donations.models import DonationTransaction, AutoRecordingSettings
from web3_integration.auto_recorder import auto_recorder
from cognizanttrust.crypto_utils import credential_manager
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Background scanner that automatically records pending transactions when auto-recording is enabled'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes
            help='Scan interval in seconds (default: 300 = 5 minutes)'
        )
        parser.add_argument(
            '--max-age',
            type=int,
            default=1440,  # 24 hours
            help='Maximum age of pending transactions to scan in minutes (default: 1440 = 24 hours)'
        )
        parser.add_argument(
            '--run-once',
            action='store_true',
            help='Run once instead of continuous background scanning'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        max_age_minutes = options['max_age']
        run_once = options['run_once']
        
        self.stdout.write(f"🤖 Starting Auto-Record Background Scanner")
        if run_once:
            self.stdout.write(f"📋 Mode: Single run")
        else:
            self.stdout.write(f"📋 Mode: Continuous (every {interval} seconds)")
        self.stdout.write(f"📋 Max transaction age: {max_age_minutes} minutes")
        
        # Main scanner loop
        while True:
            try:
                self.run_scan(max_age_minutes)
                
                if run_once:
                    self.stdout.write("✅ Single scan completed")
                    break
                
                # Wait for next scan
                self.stdout.write(f"⏳ Waiting {interval} seconds until next scan...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.stdout.write("\n🛑 Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                self.stdout.write(self.style.ERROR(f"❌ Scanner error: {e}"))
                if run_once:
                    break
                else:
                    # Wait before retrying in continuous mode
                    time.sleep(60)  # Wait 1 minute before retry
    
    def run_scan(self, max_age_minutes):
        """Run a single scan cycle"""
        # Check if auto-recording is enabled
        try:
            settings = AutoRecordingSettings.get_settings()
            if not settings.is_automatic_mode:
                self.stdout.write("ℹ️  Auto-recording disabled - skipping scan")
                return
            
            if not settings.credentials_configured:
                self.stdout.write("⚠️  No credentials configured - skipping scan")
                return
                
        except Exception as e:
            self.stdout.write(f"❌ Error checking settings: {e}")
            return
        
        # Check if credentials exist
        if not credential_manager.credentials_exist():
            self.stdout.write("⚠️  No encrypted credentials found - skipping scan")
            return
        
        # Initialize auto-recorder if not already done
        if not auto_recorder.is_initialized:
            if not auto_recorder.auto_initialize():
                self.stdout.write("❌ Could not initialize auto-recorder - skipping scan")
                return
        
        # Find pending donations
        cutoff_time = timezone.now() - timedelta(minutes=max_age_minutes)
        
        pending_donations = DonationTransaction.objects.filter(
            blockchain_status='pending',
            created_at__gte=cutoff_time
        ).exclude(
            # Skip donations that already have attempted_tx_hash (already processed)
            attempted_tx_hash__isnull=False
        ).exclude(
            attempted_tx_hash=''
        ).order_by('created_at')
        
        if not pending_donations.exists():
            self.stdout.write("✅ No new pending donations to process")
            return
        
        self.stdout.write(f"🔍 Found {pending_donations.count()} new pending donations to auto-record")
        
        recorded_count = 0
        failed_count = 0
        
        for donation in pending_donations:
            try:
                self.stdout.write(f"📝 Processing: {donation.donor_name} - ₹{donation.amount}")
                
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
                        self.stdout.write(f"   ⏳ Sent to blockchain (pending): {result.get('tx_hash')}")
                    else:
                        # Receipt received successfully
                        donation.blockchain_status = 'recorded'
                        donation.blockchain_tx_hash = result.get('tx_hash')
                        recorded_count += 1
                        self.stdout.write(f"   ✅ Successfully recorded: {result.get('tx_hash')}")
                    
                    # Update admin wallet and save
                    donation.admin_wallet = auto_recorder.account.address if auto_recorder.account else None
                    donation.save()
                    
                else:
                    failed_count += 1
                    error_msg = result.get('error', 'Unknown error')
                    self.stdout.write(f"   ❌ Failed: {error_msg}")
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(f"   ❌ Exception: {e}")
                logger.error(f"Error auto-recording donation {donation.id}: {e}")
        
        # Summary
        self.stdout.write(f"📊 Scan Summary:")
        self.stdout.write(f"   ✅ Successfully recorded: {recorded_count}")
        self.stdout.write(f"   ⏳ Sent (pending confirmation): {pending_donations.count() - recorded_count - failed_count}")
        self.stdout.write(f"   ❌ Failed: {failed_count}")
        
        if recorded_count > 0 or (pending_donations.count() - recorded_count - failed_count) > 0:
            self.stdout.write(self.style.SUCCESS(f"🎉 Processed {pending_donations.count()} pending donations!"))
        
        return {
            'total_processed': pending_donations.count(),
            'recorded_count': recorded_count,
            'failed_count': failed_count
        } 