"""
Background processor for automatic blockchain recording
Implements 3-thread system for donation processing
"""
import threading
import time
import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from .models import DonationTransaction, AutoRecordingSettings
from cognizanttrust.crypto_utils import credential_manager
from web3_integration.auto_recorder import auto_recorder

logger = logging.getLogger(__name__)

class BackgroundProcessor:
    def __init__(self):
        self.running = False
        self.threads = {}
        self.donation_queue = []
        self.queue_lock = threading.Lock()
        self.last_pending_scan = None
        self.last_verification_scan = None
        
        # Enhanced monitoring data
        self.current_processing = {
            'donation_recorder': None,
            'pending_processor': None,
            'timeout_verifier': None
        }
        self.processing_history = []
        self.thread_activity_logs = {
            'donation_recorder': [],
            'pending_processor': [],
            'timeout_verifier': []
        }
        self.statistics = {
            'total_processed': 0,
            'successful_recordings': 0,
            'timeout_recordings': 0,
            'failed_recordings': 0,
            'queue_max_size': 0
        }

    def _log_activity(self, thread_name, message, level='info'):
        """Log thread activity with timestamp"""
        timestamp = timezone.now()
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'level': level
        }
        
        # Keep only last 50 entries per thread
        if len(self.thread_activity_logs[thread_name]) >= 50:
            self.thread_activity_logs[thread_name].pop(0)
        
        self.thread_activity_logs[thread_name].append(log_entry)
        
        # Also log to Django logger
        getattr(logger, level)(f"[{thread_name.upper()}] {message}")

    def _set_current_processing(self, thread_name, donation_id=None, details=None):
        """Set what the thread is currently processing"""
        self.current_processing[thread_name] = {
            'donation_id': donation_id,
            'details': details,
            'started_at': timezone.now() if donation_id else None
        }

    def _clear_current_processing(self, thread_name):
        """Clear current processing status"""
        self.current_processing[thread_name] = None

    def is_auto_mode_enabled(self):
        """Check if auto mode is enabled and credentials are configured"""
        try:
            settings = AutoRecordingSettings.get_settings()
            if not settings.is_automatic_mode:
                return False
            
            # Check if credentials are available
            if not credential_manager.credentials_exist():
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error checking auto mode: {e}")
            return False

    def start_all_threads(self):
        """Start all background threads"""
        if self.running:
            logger.warning("Background processor already running")
            return
            
        if not self.is_auto_mode_enabled():
            logger.info("🔴 Auto mode not enabled - background processor not started")
            logger.info("💡 To enable: Go to Admin Dashboard → Toggle Auto Mode ON")
            return

        self.running = True
        
        # Thread 1: Donation Recording (always active)
        self.threads['donation_recorder'] = threading.Thread(
            target=self._donation_recording_loop, 
            name="DonationRecorder"
        )
        self.threads['donation_recorder'].daemon = True
        self.threads['donation_recorder'].start()
        
        # Thread 2: Pending Processing (periodic)
        self.threads['pending_processor'] = threading.Thread(
            target=self._pending_processing_loop, 
            name="PendingProcessor"
        )
        self.threads['pending_processor'].daemon = True
        self.threads['pending_processor'].start()
        
        # Thread 3: Timeout Verification (periodic)
        self.threads['timeout_verifier'] = threading.Thread(
            target=self._timeout_verification_loop, 
            name="TimeoutVerifier"
        )
        self.threads['timeout_verifier'].daemon = True
        self.threads['timeout_verifier'].start()
        
        logger.info("🚀 All 3 background threads started successfully")
        self._log_activity('donation_recorder', 'Thread started - monitoring donation queue')
        self._log_activity('pending_processor', 'Thread started - periodic pending transaction processing')
        self._log_activity('timeout_verifier', 'Thread started - periodic timeout verification')

    def stop_all_threads(self):
        """Stop all background threads gracefully"""
        if not self.running:
            return
            
        logger.info("🛑 Stopping all background threads...")
        self.running = False
        
        # Wait for threads to finish
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                logger.info(f"⏳ Waiting for {thread_name} to stop...")
                thread.join(timeout=10)
                if thread.is_alive():
                    logger.warning(f"⚠️ {thread_name} did not stop gracefully")
                else:
                    logger.info(f"✅ {thread_name} stopped")
                    
        self.threads.clear()
        logger.info("🏁 All background threads stopped")

    def add_donation_to_queue(self, donation_id):
        """Add donation to processing queue (thread-safe)"""
        with self.queue_lock:
            if donation_id not in self.donation_queue:
                self.donation_queue.append(donation_id)
                
                # Update queue statistics
                if len(self.donation_queue) > self.statistics['queue_max_size']:
                    self.statistics['queue_max_size'] = len(self.donation_queue)
                
                self._log_activity('donation_recorder', f'Added donation {donation_id} to queue (queue size: {len(self.donation_queue)})')
                logger.info(f"📝 Added donation {donation_id} to processing queue")

    def _donation_recording_loop(self):
        """Thread 1: Process donations from queue and handle new submissions"""
        self._log_activity('donation_recorder', 'Starting donation recording loop')
        
        while self.running:
            try:
                if not self.is_auto_mode_enabled():
                    self._log_activity('donation_recorder', 'Auto mode disabled - pausing', 'warning')
                    time.sleep(30)
                    continue

                # Check if there are donations in queue
                donation_to_process = None
                with self.queue_lock:
                    if self.donation_queue:
                        donation_to_process = self.donation_queue.pop(0)

                if donation_to_process:
                    self._set_current_processing('donation_recorder', donation_to_process, 'Recording new donation on blockchain')
                    self._log_activity('donation_recorder', f'Processing donation {donation_to_process} from queue')
                    success = self._process_single_donation(donation_to_process)
                    
                    if success:
                        self.statistics['successful_recordings'] += 1
                        self._log_activity('donation_recorder', f'Successfully recorded donation {donation_to_process}', 'info')
                    else:
                        self.statistics['failed_recordings'] += 1
                        self._log_activity('donation_recorder', f'Failed to record donation {donation_to_process}', 'warning')
                    
                    self.statistics['total_processed'] += 1
                    self._clear_current_processing('donation_recorder')
                
                # Also check for any pending donations without attempted_tx_hash (missed by queue)
                try:
                    missed_donations = DonationTransaction.objects.filter(
                        blockchain_status='pending',
                        attempted_tx_hash__isnull=True
                    ).order_by('timestamp')[:5]  # Process 5 at a time to avoid overload
                    
                    for donation in missed_donations:
                        self._set_current_processing('donation_recorder', donation.id, 'Processing missed pending donation')
                        self._log_activity('donation_recorder', f'Processing missed donation {donation.id}')
                        success = self._process_single_donation(donation.id)
                        
                        if success:
                            self.statistics['successful_recordings'] += 1
                        else:
                            self.statistics['failed_recordings'] += 1
                        
                        self.statistics['total_processed'] += 1
                        self._clear_current_processing('donation_recorder')
                        
                except Exception as e:
                    self._log_activity('donation_recorder', f'Error checking missed donations: {str(e)}', 'error')

                # Sleep for 5 seconds before next iteration
                time.sleep(5)
                
            except Exception as e:
                self._log_activity('donation_recorder', f'Error in donation recording loop: {str(e)}', 'error')
                self._clear_current_processing('donation_recorder')
                time.sleep(10)

    def _pending_processing_loop(self):
        """Thread 2: Process pending donations (network failures, retries)"""
        self._log_activity('pending_processor', 'Starting pending processing loop')
        
        while self.running:
            try:
                if not self.is_auto_mode_enabled():
                    self._log_activity('pending_processor', 'Auto mode disabled - pausing', 'warning')
                    time.sleep(60)
                    continue

                self._set_current_processing('pending_processor', None, 'Scanning for pending transactions to retry')
                self._log_activity('pending_processor', 'Scanning for pending transactions to retry')
                
                # Get ALL pending donations without attempted_tx_hash (network failures)
                # Scan entire database - no time limit
                pending_donations = DonationTransaction.objects.filter(
                    blockchain_status='pending',
                    attempted_tx_hash__isnull=True
                ).order_by('timestamp')[:10]  # Process 10 at a time to avoid overload
                
                if pending_donations.exists():
                    self._log_activity('pending_processor', f'Found {pending_donations.count()} pending transactions to retry')
                    
                    for donation in pending_donations:
                        if not self.running:
                            break
                            
                        self._set_current_processing('pending_processor', donation.id, 'Retrying blockchain recording')
                        self._log_activity('pending_processor', f'Retrying donation {donation.id}')
                        success = self._process_single_donation(donation.id)
                        
                        if success:
                            self.statistics['successful_recordings'] += 1
                            self._log_activity('pending_processor', f'Successfully retried donation {donation.id}', 'info')
                        else:
                            self.statistics['failed_recordings'] += 1
                            self._log_activity('pending_processor', f'Retry failed for donation {donation.id}', 'warning')
                        
                        self.statistics['total_processed'] += 1
                        self._clear_current_processing('pending_processor')
                        time.sleep(2)  # Small delay between retries
                else:
                    self._log_activity('pending_processor', 'No pending transactions found for retry')
                
                self.last_pending_scan = timezone.now()
                self._clear_current_processing('pending_processor')
                
                # Sleep for 2 minutes before next scan
                time.sleep(120)
                
            except Exception as e:
                self._log_activity('pending_processor', f'Error in pending processing loop: {str(e)}', 'error')
                self._clear_current_processing('pending_processor')
                time.sleep(60)

    def _timeout_verification_loop(self):
        """Thread 3: Verify timed-out transactions"""
        self._log_activity('timeout_verifier', 'Starting timeout verification loop')
        
        while self.running:
            try:
                self._set_current_processing('timeout_verifier', None, 'Verifying timed-out transactions')
                self._log_activity('timeout_verifier', 'Starting timeout verification scan')
                
                # Import and run the verification logic
                from .auto_verifier import AutoVerifier
                verifier = AutoVerifier()
                verifier.verify_pending_transactions()
                
                self.last_verification_scan = timezone.now()
                self._log_activity('timeout_verifier', 'Completed timeout verification scan')
                self._clear_current_processing('timeout_verifier')
                
                # Sleep for 5 minutes before next verification
                time.sleep(300)
                
            except Exception as e:
                self._log_activity('timeout_verifier', f'Error in timeout verification loop: {str(e)}', 'error')
                self._clear_current_processing('timeout_verifier')
                time.sleep(60)

    def _process_single_donation(self, donation_id):
        """Process a single donation on blockchain"""
        try:
            donation = DonationTransaction.objects.get(id=donation_id)
            
            # Check and fix missing UPI ref ID (for old test data)
            if not donation.upi_ref_id or donation.upi_ref_id.strip() == '':
                import uuid
                donation.upi_ref_id = f"UPI{uuid.uuid4().hex[:8].upper()}"
                donation.save()
                self._log_activity('donation_recorder', f'Generated UPI ref ID for donation {donation_id}: {donation.upi_ref_id}', 'info')
            
            # Initialize auto recorder if needed
            if not auto_recorder.is_initialized:
                if not auto_recorder.initialize():
                    logger.error(f"Could not initialize auto recorder for donation {donation_id}")
                    return False
            
            # Record on blockchain
            result = auto_recorder.record_donation_automatically(
                donor_name=donation.donor_name,
                amount=float(donation.amount),
                purpose=donation.purpose,
                upi_ref_id=donation.upi_ref_id
            )
            
            success = result.get('success', False)
            tx_hash = result.get('tx_hash')
            
            if success:
                # Update donation status
                with transaction.atomic():
                    donation.refresh_from_db()
                    donation.blockchain_status = 'recorded'
                    donation.attempted_tx_hash = tx_hash
                    donation.save()
                
                logger.info(f"✅ Donation {donation_id} recorded successfully on blockchain")
                return True
            else:
                # Keep as pending for retry (don't mark as failed)
                if tx_hash:  # Timeout case
                    with transaction.atomic():
                        donation.refresh_from_db()
                        donation.attempted_tx_hash = tx_hash
                        donation.save()
                    self.statistics['timeout_recordings'] += 1
                    logger.warning(f"⏰ Donation {donation_id} timed out, marked for verification")
                else:
                    logger.warning(f"❌ Donation {donation_id} failed to record, will retry later")
                
                return False
                
        except DonationTransaction.DoesNotExist:
            logger.error(f"Donation {donation_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error processing donation {donation_id}: {str(e)}")
            return False

    def get_detailed_status(self):
        """Get comprehensive status information for monitoring"""
        try:
            # Get current queue size
            with self.queue_lock:
                current_queue_size = len(self.donation_queue)
                current_queue = self.donation_queue.copy()
            
            # Get database statistics
            pending_count = DonationTransaction.objects.filter(blockchain_status='pending').count()
            timedout_count = DonationTransaction.objects.filter(
                blockchain_status='pending',
                attempted_tx_hash__isnull=False
            ).count()
            
            return {
                'success': True,
                'status': {
                    'running': self.running,
                    'auto_mode_enabled': self.is_auto_mode_enabled(),
                    'threads': {
                        name: thread.is_alive() if thread else False 
                        for name, thread in self.threads.items()
                    },
                    'current_processing': self.current_processing,
                    'queue': {
                        'size': current_queue_size,
                        'donations': current_queue,
                        'max_size_today': self.statistics['queue_max_size']
                    },
                    'database_stats': {
                        'pending_donations': pending_count,
                        'timedout_donations': timedout_count
                    },
                    'processing_stats': self.statistics,
                    'last_scans': {
                        'pending_scan': self.last_pending_scan.isoformat() if self.last_pending_scan else None,
                        'verification_scan': self.last_verification_scan.isoformat() if self.last_verification_scan else None
                    },
                    'activity_logs': self.thread_activity_logs
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_status(self):
        """Get basic status information (for existing endpoint compatibility)"""
        try:
            with self.queue_lock:
                queue_size = len(self.donation_queue)
            
            return {
                'success': True,
                'status': {
                    'running': self.running,
                    'auto_mode_enabled': self.is_auto_mode_enabled(),
                    'threads': {
                        name: thread.is_alive() if thread else False 
                        for name, thread in self.threads.items()
                    },
                    'queue_size': queue_size,
                    'last_pending_scan': self.last_pending_scan.isoformat() if self.last_pending_scan else None,
                    'last_verification_scan': self.last_verification_scan.isoformat() if self.last_verification_scan else None
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global background processor instance
background_processor = BackgroundProcessor()

def start_background_processor():
    """Start the background processor"""
    background_processor.start_all_threads()

def stop_background_processor():
    """Stop the background processor"""
    background_processor.stop_all_threads()

def add_donation_to_queue(donation_id):
    """Add donation to processing queue"""
    background_processor.add_donation_to_queue(donation_id)

def get_processor_status():
    """Get processor status"""
    return background_processor.get_status() 