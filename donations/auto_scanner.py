"""
Auto-scanner module for background processing of pending donations
"""

import logging
from datetime import timedelta
from django.utils import timezone
from .models import DonationTransaction, AutoRecordingSettings
from cognizanttrust.crypto_utils import credential_manager

logger = logging.getLogger(__name__)

def scan_and_record_pending(max_age_hours=1, max_transactions=5):
    """
    Scan for pending donations and automatically record them if auto-mode is enabled
    
    Args:
        max_age_hours: Only scan transactions newer than this many hours
        max_transactions: Maximum number of transactions to process in one scan
        
    Returns:
        dict: Results of the scan
    """
    try:
        # Check if auto-recording is enabled
        settings = AutoRecordingSettings.get_settings()
        if not settings.is_automatic_mode:
            return {'success': False, 'message': 'Auto-recording is disabled'}
        
        if not settings.credentials_configured:
            return {'success': False, 'message': 'No credentials configured'}
        
        # Check if credentials exist
        if not credential_manager.credentials_exist():
            return {'success': False, 'message': 'No encrypted credentials found'}
        
        # Initialize auto-recorder if not already done
        from web3_integration.auto_recorder import auto_recorder
        
        if not auto_recorder.is_initialized:
            if not auto_recorder.auto_initialize():
                return {'success': False, 'message': 'Could not initialize auto-recorder'}
        
        # Find pending donations that need processing
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        # Get two types of pending donations:
        # 1. Never attempted (no attempted_tx_hash)
        # 2. Previously attempted but still pending (need verification)
        never_attempted = DonationTransaction.objects.filter(
            blockchain_status='pending',
            created_at__gte=cutoff_time,
            attempted_tx_hash__isnull=True
        )
        
        need_verification = DonationTransaction.objects.filter(
            blockchain_status='pending',
            created_at__gte=cutoff_time,
            attempted_tx_hash__isnull=False
        ).exclude(attempted_tx_hash='')
        
        # Combine and limit
        pending_donations = list(never_attempted[:max_transactions//2]) + list(need_verification[:max_transactions//2])
        pending_donations = pending_donations[:max_transactions]
        
        if not pending_donations:
            return {
                'success': True, 
                'message': 'No new pending donations to process',
                'processed_count': 0,
                'recorded_count': 0
            }
        
        logger.info(f"🔍 Auto-scanner found {len(pending_donations)} pending donations to process")
        
        recorded_count = 0
        failed_count = 0
        results = []
        
        for donation in pending_donations:
            try:
                logger.info(f"📝 Processing: {donation.donor_name} - ₹{donation.amount}")
                
                # Check if this donation already has an attempted_tx_hash (needs verification)
                if donation.attempted_tx_hash:
                    logger.info(f"🔍 Verifying existing transaction: {donation.attempted_tx_hash}")
                    
                    # Try to get receipt for existing transaction
                    try:
                        if auto_recorder.w3:
                            receipt = auto_recorder.w3.eth.get_transaction_receipt(donation.attempted_tx_hash)
                            
                            if receipt and receipt.status == 1:
                                # Transaction was successful
                                donation.blockchain_status = 'recorded'
                                donation.blockchain_tx_hash = donation.attempted_tx_hash
                                donation.save()
                                recorded_count += 1
                                
                                results.append({
                                    'donation_id': str(donation.id),
                                    'donor_name': donation.donor_name,
                                    'status': 'verified_successful',
                                    'tx_hash': donation.attempted_tx_hash
                                })
                                
                                logger.info(f"✅ Verified successful: {donation.donor_name} -> {donation.attempted_tx_hash}")
                                continue
                                
                            elif receipt and receipt.status == 0:
                                # Transaction failed
                                logger.warning(f"❌ Transaction failed on blockchain: {donation.attempted_tx_hash}")
                                # Don't continue - will try to re-record below
                            else:
                                logger.info(f"⏳ Transaction still pending verification: {donation.attempted_tx_hash}")
                                continue
                    except Exception as verify_error:
                        logger.warning(f"Could not verify transaction {donation.attempted_tx_hash}: {verify_error}")
                        # Continue to try re-recording
                
                # If no attempted_tx_hash OR verification failed, try to record
                logger.info(f"🚀 Auto-recording: {donation.donor_name} - ₹{donation.amount}")
                
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
                        status = 'sent_pending'
                    else:
                        # Receipt received successfully
                        donation.blockchain_status = 'recorded'
                        donation.blockchain_tx_hash = result.get('tx_hash')
                        recorded_count += 1
                        status = 'recorded'
                    
                    # Update admin wallet and save
                    donation.admin_wallet = auto_recorder.account.address if auto_recorder.account else None
                    donation.save()
                    
                    results.append({
                        'donation_id': str(donation.id),
                        'donor_name': donation.donor_name,
                        'status': status,
                        'tx_hash': result.get('tx_hash')
                    })
                    
                    logger.info(f"✅ Auto-recorded: {donation.donor_name} -> {result.get('tx_hash')}")
                    
                else:
                    failed_count += 1
                    error_msg = result.get('error', 'Unknown error')
                    
                    results.append({
                        'donation_id': str(donation.id),
                        'donor_name': donation.donor_name,
                        'status': 'failed',
                        'error': error_msg
                    })
                    
                    logger.warning(f"❌ Failed to auto-record {donation.donor_name}: {error_msg}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Exception processing donation {donation.id}: {e}")
                
                results.append({
                    'donation_id': str(donation.id),
                    'donor_name': donation.donor_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'success': True,
            'message': f'Processed {len(pending_donations)} pending donations',
            'processed_count': len(pending_donations),
            'recorded_count': recorded_count,
            'failed_count': failed_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in auto-scanner: {e}")
        return {'success': False, 'message': f'Scanner error: {str(e)}'}


def is_auto_scanner_enabled():
    """Check if auto-scanning should be enabled"""
    try:
        settings = AutoRecordingSettings.get_settings()
        return (settings.is_automatic_mode and 
                settings.credentials_configured and 
                credential_manager.credentials_exist())
    except Exception:
        return False 