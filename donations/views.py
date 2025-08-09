from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json
import uuid
from decimal import Decimal
from .models import DonationTransaction, DonationSpending, AutoRecordingSettings
from cognizanttrust.crypto_utils import credential_manager
from cognizanttrust.security_config import security_manager
from web3_integration.auto_recorder import auto_recorder
import logging
from django.utils import timezone
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .forms import DonorRegistrationForm, LoginForm, UserDonationForm, DonorProfileForm
from .models import DonorProfile
import time
import uuid
from django.db import IntegrityError
import json
import decimal
from decimal import Decimal

logger = logging.getLogger(__name__)

def home(request):
    """Home page with real impact statistics from database"""
    from django.db.models import Sum, Count
    
    # Get real statistics from database
    total_donations = DonationTransaction.objects.filter(
        blockchain_status__in=['pending', 'recorded']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_donors = DonationTransaction.objects.filter(
        blockchain_status__in=['pending', 'recorded']
    ).values('donor_name').distinct().count()
    
    total_spending = DonationSpending.objects.filter(
        blockchain_status__in=['pending', 'recorded']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate lives impacted (assuming ₹1000 impacts 1 life on average)
    lives_impacted = int(total_spending / 1000) if total_spending > 0 else 0
    
    # Format amounts for display
    def format_amount(amount):
        if amount >= 100000:  # 1 Lakh or more
            return f"₹{amount/100000:.1f}L"
        elif amount >= 1000:  # 1 Thousand or more
            return f"₹{amount/1000:.1f}K"
        else:
            return f"₹{amount:.0f}"
    
    context = {
        'total_donations': format_amount(total_donations),
        'total_donations_raw': total_donations,
        'total_donors': total_donors,
        'total_spending': format_amount(total_spending),
        'lives_impacted': lives_impacted,
        'transparency_percent': 100 if total_donations > 0 else 0,
    }
    
    return render(request, 'donations/home.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def submit_donation(request):
    """Handle donation submission (mocked payment) - works for both authenticated and anonymous users"""
    try:
        data = json.loads(request.body)
        donor_name = data.get('donor_name', '').strip()
        amount = data.get('amount', '')
        purpose = data.get('purpose', '').strip()
        
        # Validation
        if not donor_name:
            return JsonResponse({'success': False, 'error': 'Donor name is required'})
        if not amount or float(amount) <= 0:
            return JsonResponse({'success': False, 'error': 'Valid amount is required'})
        if not purpose:
            return JsonResponse({'success': False, 'error': 'Purpose is required'})
        
        # Generate mock UPI reference ID
        upi_ref_id = f"UPI{uuid.uuid4().hex[:8].upper()}"
        
        # Create donation transaction - link to user if authenticated
        donation_data = {
            'donor_name': donor_name,
            'amount': Decimal(str(amount)),
            'purpose': purpose,
            'upi_ref_id': upi_ref_id,
            'blockchain_status': 'pending'
        }
        
        # If user is authenticated, link the donation
        if request.user.is_authenticated:
            donation_data['donor'] = request.user
            donation_data['donor_email'] = request.user.email
            if hasattr(request.user, 'donor_profile'):
                donation_data['donor_phone'] = request.user.donor_profile.phone_number
        
        donation = DonationTransaction.objects.create(**donation_data)
        
        # 🚀 NEW: Check if automatic recording is enabled
        settings = AutoRecordingSettings.get_settings()
        if settings.is_automatic_mode:
            # 🎯 Add donation to Thread 1 processing queue
            try:
                from .background_processor import add_donation_to_queue
                add_donation_to_queue(donation.id)
                logger.info(f"📝 Added donation {donation.id} to background processing queue")
            except Exception as e:
                logger.error(f"❌ Error adding donation to queue: {e}")
                # Continue with normal processing
            # Note: Auto recorder initialization and processing is now handled by background threads
            # The donation has been added to the queue and will be processed automatically
            return JsonResponse({
                'success': True,
                'message': 'Donation successful! Your donation will be automatically recorded on blockchain.',
                'auto_recorded': True,
                'queued_for_processing': True,
                'donation': {
                    'donor_name': donation.donor_name,
                    'amount': str(donation.amount),
                    'purpose': donation.purpose,
                    'upi_ref_id': donation.upi_ref_id,
                    'transaction_id': str(donation.id),
                    'blockchain_status': donation.blockchain_status
                }
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Donation successful! Thank you for your contribution.',
            'auto_recorded': False,
            'donation': {
                'donor_name': donation.donor_name,
                'amount': str(donation.amount),
                'purpose': donation.purpose,
                'upi_ref_id': donation.upi_ref_id,
                'transaction_id': str(donation.id)
            }
        })
        
    except Exception as e:
        logger.error(f"Donation submission error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def admin_dashboard(request):
    """Admin dashboard showing all donations and spendings"""
    # Handle login form submission
    if request.method == 'POST' and 'login' in request.POST:
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            messages.success(request, f'Welcome Admin {user.get_full_name() or user.username}!')
            return redirect('/admin/')
        else:
            if user and not (user.is_staff or user.is_superuser):
                messages.error(request, 'You are not an admin user. Please use Donor Login.')
                return redirect('donations:user_login')
            else:
                messages.error(request, 'Invalid admin credentials.')
    
    # Check if user is authenticated and is admin
    if not request.user.is_authenticated:
        # Show admin login form
        return render(request, 'donations/admin_login.html')
    
    if not (request.user.is_staff or request.user.is_superuser):
        # User is authenticated but not admin - redirect to donor dashboard
        messages.info(request, 'Redirecting you to your donor dashboard.')
        return redirect('donations:user_dashboard')
    
    donations = DonationTransaction.objects.all()
    spendings = DonationSpending.objects.all()
    
    # Get auto recording settings
    settings = AutoRecordingSettings.get_settings()
    
    # Calculate donation statistics
    total_donations = donations.count()
    recorded_donations_count = donations.filter(blockchain_status='recorded').count()
    
    # Separate pending transactions: truly pending vs timed out
    all_pending = donations.filter(blockchain_status='pending')
    pending_donations_count = all_pending.filter(attempted_tx_hash__isnull=True).count()  # Never attempted
    timedout_donations_count = all_pending.exclude(attempted_tx_hash__isnull=True).exclude(attempted_tx_hash='').count()  # Has tx_hash but still pending
    
    total_donated_amount = sum(donation.amount for donation in donations)
    
    # Calculate spending statistics
    total_spendings = spendings.count()
    recorded_spendings_count = spendings.filter(blockchain_status='recorded').count()
    pending_spendings_count = spendings.filter(blockchain_status='pending').count()
    failed_spendings_count = spendings.filter(blockchain_status='failed').count()
    total_spent_amount = sum(spending.amount for spending in spendings)
    
    # Calculate remaining balance
    remaining_balance = total_donated_amount - total_spent_amount
    
    context = {
        'donations': donations[:10],  # Show recent 10 donations
        'spendings': spendings[:5],   # Show recent 5 spendings
        'total_donations': total_donations,
        'recorded_donations_count': recorded_donations_count,
        'pending_donations_count': pending_donations_count,
        'timedout_donations_count': timedout_donations_count,  # 🚀 NEW: Separate timed out count
        'total_donated_amount': total_donated_amount,
        'total_spendings': total_spendings,
        'recorded_spendings_count': recorded_spendings_count,
        'pending_spendings_count': pending_spendings_count,
        'failed_spendings_count': failed_spendings_count,
        'total_spent_amount': total_spent_amount,
        'remaining_balance': remaining_balance,
        'auto_settings': settings,  # 🚀 NEW: Pass settings to template
        'credentials_exist': credential_manager.credentials_exist(),  # 🚀 NEW
    }
    
    return render(request, 'donations/admin_dashboard.html', context)

def admin_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/admin/')

@csrf_exempt
@require_http_methods(["POST"])
def store_wallet_credentials(request):
    """🚀 NEW: Store encrypted wallet credentials for automatic mode"""
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        data = json.loads(request.body)
        private_key = data.get('private_key', '').strip()
        wallet_address = data.get('wallet_address', '').strip()
        master_password = data.get('master_password', '').strip()
        
        # Get client IP for security logging
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Validate master password strength
        password_validation = security_manager.validate_master_password(master_password)
        if not password_validation['valid']:
            security_manager.audit_log('WEAK_PASSWORD_ATTEMPT', request.user.username, client_ip)
            return JsonResponse({
                'success': False, 
                'error': 'Password not strong enough for production',
                'validation': password_validation
            })
        
        # Validate inputs
        if not private_key or not wallet_address or not master_password:
            return JsonResponse({'success': False, 'error': 'All fields are required'})
        
        # Validate wallet address format
        if not wallet_address.startswith('0x') or len(wallet_address) != 42:
            return JsonResponse({'success': False, 'error': 'Invalid wallet address format'})
        
        # Clean private key (remove 0x prefix if present)
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        
        if len(private_key) != 64:
            return JsonResponse({'success': False, 'error': 'Invalid private key format'})
        
        # Store encrypted credentials
        success = credential_manager.store_credentials(private_key, wallet_address, master_password)
        
        if success:
            # Update settings
            settings = AutoRecordingSettings.get_settings()
            settings.credentials_configured = True
            settings.last_modified_by = request.user.username
            settings.save()
            
            # Security audit log
            security_manager.audit_log('CREDENTIALS_STORED', request.user.username, client_ip, {
                'wallet_address': wallet_address
            })
            
            return JsonResponse({
                'success': True,
                'message': 'Credentials stored securely with AES-256 encryption'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to store credentials'})
            
    except Exception as e:
        logger.error(f"Credential storage error: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

@csrf_exempt
@require_http_methods(["POST"])
def toggle_recording_mode(request):
    """🚀 NEW: Toggle between manual and automatic recording modes"""
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        data = json.loads(request.body)
        logger.info(f"🔍 Toggle mode called with data: {data}")
        
        mode = (data.get('mode') or '').strip()
        master_password = (data.get('master_password') or '').strip()
        
        logger.info(f"🔍 Parsed mode: '{mode}', password provided: {bool(master_password)}")
        
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        if mode not in ['manual', 'automatic']:
            return JsonResponse({'success': False, 'error': 'Invalid mode'})
        
        settings = AutoRecordingSettings.get_settings()
        
        if mode == 'automatic':
            # Switching to automatic mode requires password verification
            if not master_password:
                return JsonResponse({'success': False, 'error': 'Master password required for automatic mode'})
            
            # Verify credentials can be loaded
            credentials = credential_manager.load_credentials(master_password)
            if not credentials:
                security_manager.record_failed_attempt(client_ip, request.user.username)
                return JsonResponse({'success': False, 'error': 'Invalid master password or no credentials stored'})
            
            # Initialize auto recorder
            print(f"🚀 Attempting to initialize auto recorder...")
            if not auto_recorder.initialize(master_password):
                error_msg = 'Failed to initialize automatic recorder. Check console logs for details.'
                print(f"❌ Auto recorder initialization failed")
                return JsonResponse({'success': False, 'error': error_msg})
            
            # Store session password for auto-reinitialization (in memory only)
            auto_recorder.set_session_password(master_password)
            print(f"✅ Session password stored for auto-reinitialization")
            
            # Update settings
            settings.recording_mode = 'automatic'
            settings.auto_recording_enabled = True
            settings.last_auto_session = timezone.now()
            
            security_manager.audit_log('AUTO_MODE_ENABLED', request.user.username, client_ip)
            
        else:
            # Switching to manual mode
            settings.recording_mode = 'manual'
            settings.auto_recording_enabled = False
            
            # Clear session password for security
            auto_recorder.clear_session_password()
            print(f"✅ Session password cleared for security")
            
            security_manager.audit_log('MANUAL_MODE_ENABLED', request.user.username, client_ip)
        
        settings.last_modified_by = request.user.username
        settings.save()
        
        security_manager.clear_failed_attempts(client_ip, request.user.username)
        
        return JsonResponse({
            'success': True,
            'mode': settings.recording_mode,
            'message': f'Recording mode switched to {settings.get_recording_mode_display()}',
            'security_status': settings.security_status
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in toggle mode: {e}")
        logger.error(f"Request body: {request.body}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Mode toggle error: {e}")
        logger.error(f"Request body: {request.body}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

@csrf_exempt
@require_http_methods(["POST"])
def delete_credentials(request):
    """🚀 NEW: Securely delete stored credentials"""
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        data = json.loads(request.body)
        confirm = data.get('confirm', False)
        
        if not confirm:
            return JsonResponse({'success': False, 'error': 'Confirmation required'})
        
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Delete credentials
        success = credential_manager.delete_credentials()
        
        if success:
            # Update settings
            settings = AutoRecordingSettings.get_settings()
            settings.credentials_configured = False
            settings.recording_mode = 'manual'
            settings.auto_recording_enabled = False
            settings.last_modified_by = request.user.username
            settings.save()
            
            security_manager.audit_log('CREDENTIALS_DELETED', request.user.username, client_ip)
            
            return JsonResponse({
                'success': True,
                'message': 'Credentials deleted securely'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to delete credentials'})
            
    except Exception as e:
        logger.error(f"Credential deletion error: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

@csrf_exempt
@require_http_methods(["POST"])
def record_on_blockchain(request):
    """Handle blockchain recording request"""
    print(f"=== RECORD ON BLOCKCHAIN API CALLED ===")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User is staff: {request.user.is_staff if request.user.is_authenticated else 'N/A'}")
    print(f"Request body: {request.body}")
    
    # Check admin authentication for API calls
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        print("❌ Authentication failed")
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        data = json.loads(request.body)
        print(f"Parsed data: {data}")
        
        transaction_id = data.get('transaction_id')
        tx_hash = data.get('tx_hash')
        admin_wallet = data.get('admin_wallet')
        
        print(f"Transaction ID: {transaction_id}")
        print(f"TX Hash: {tx_hash}")
        print(f"Admin Wallet: {admin_wallet}")
        
        if not all([transaction_id, tx_hash, admin_wallet]):
            print("❌ Missing required data")
            return JsonResponse({'success': False, 'error': 'Missing required data'})
        
        donation = get_object_or_404(DonationTransaction, id=transaction_id)
        print(f"Found donation: {donation.donor_name} - Current status: {donation.blockchain_status}")
        
        # Update blockchain status
        old_status = donation.blockchain_status
        donation.blockchain_status = 'recorded'
        donation.blockchain_tx_hash = tx_hash
        donation.admin_wallet = admin_wallet
        donation.save()
        
        # Verify the save worked by reloading from database
        donation.refresh_from_db()
        print(f"✅ Updated donation status from '{old_status}' to '{donation.blockchain_status}'")
        print(f"✅ TX Hash saved: {donation.blockchain_tx_hash}")
        print(f"✅ Admin wallet saved: {donation.admin_wallet}")
        
        # Double-check by querying database again
        verification = DonationTransaction.objects.get(id=transaction_id)
        print(f"🔍 Database verification - Status: {verification.blockchain_status}, TX: {verification.blockchain_tx_hash}")
        
        return JsonResponse({
            'success': True,
            'message': 'Transaction recorded on blockchain successfully!',
            'tx_hash': tx_hash,
            'database_status': verification.blockchain_status
        })
        
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def update_blockchain_status(request):
    """Update blockchain status for a transaction"""
    # Check admin authentication for API calls
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        
        if not all([transaction_id, status]):
            return JsonResponse({'success': False, 'error': 'Missing required data'})
        
        donation = get_object_or_404(DonationTransaction, id=transaction_id)
        donation.blockchain_status = status
        donation.save()
        
        return JsonResponse({'success': True, 'message': 'Status updated successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def submit_spending(request):
    """Handle spending submission"""
    # Check admin authentication
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()
        amount = data.get('amount', '')
        beneficiaries = data.get('beneficiaries', '').strip()
        location = data.get('location', '').strip()
        receipt_reference = data.get('receipt_reference', '').strip()
        
        # Validation
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'})
        if not description:
            return JsonResponse({'success': False, 'error': 'Description is required'})
        if not category:
            return JsonResponse({'success': False, 'error': 'Category is required'})
        if not amount or float(amount) <= 0:
            return JsonResponse({'success': False, 'error': 'Valid amount is required'})
        if not beneficiaries:
            return JsonResponse({'success': False, 'error': 'Beneficiaries information is required'})
        if not location:
            return JsonResponse({'success': False, 'error': 'Location is required'})
        
        # Check if sufficient balance is available
        total_donations = sum(d.amount for d in DonationTransaction.objects.all())
        total_spendings = sum(s.amount for s in DonationSpending.objects.all())
        available_balance = total_donations - total_spendings
        
        if Decimal(str(amount)) > available_balance:
            return JsonResponse({
                'success': False, 
                'error': f'Insufficient balance. Available: ₹{available_balance}, Requested: ₹{amount}'
            })
        
        # Create spending record
        spending = DonationSpending.objects.create(
            title=title,
            description=description,
            category=category,
            amount=Decimal(str(amount)),
            beneficiaries=beneficiaries,
            location=location,
            receipt_reference=receipt_reference if receipt_reference else None,
            blockchain_status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Spending record created successfully!',
            'spending': {
                'id': str(spending.id),
                'title': spending.title,
                'amount': str(spending.amount),
                'category': spending.get_category_display(),
                'beneficiaries': spending.beneficiaries,
                'location': spending.location
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def record_spending_on_blockchain(request):
    """Handle blockchain spending recording request"""
    print(f"=== RECORD SPENDING ON BLOCKCHAIN API CALLED ===")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User is staff: {request.user.is_staff if request.user.is_authenticated else 'N/A'}")
    print(f"Request body: {request.body}")
    
    # Check admin authentication for API calls
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        print("❌ Authentication failed")
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        data = json.loads(request.body)
        print(f"Parsed data: {data}")
        
        spending_id = data.get('spending_id')
        tx_hash = data.get('tx_hash')
        admin_wallet = data.get('admin_wallet')
        
        print(f"Spending ID: {spending_id}")
        print(f"TX Hash: {tx_hash}")
        print(f"Admin Wallet: {admin_wallet}")
        
        if not all([spending_id, tx_hash, admin_wallet]):
            print("❌ Missing required data")
            return JsonResponse({'success': False, 'error': 'Missing required data'})
        
        spending = get_object_or_404(DonationSpending, id=spending_id)
        print(f"Found spending: {spending.title} - Current status: {spending.blockchain_status}")
        
        # Update blockchain status
        old_status = spending.blockchain_status
        spending.blockchain_status = 'recorded'
        spending.blockchain_tx_hash = tx_hash
        spending.admin_wallet = admin_wallet
        spending.save()
        
        # Verify the save worked by reloading from database
        spending.refresh_from_db()
        print(f"✅ Updated spending status from '{old_status}' to '{spending.blockchain_status}'")
        print(f"✅ TX Hash saved: {spending.blockchain_tx_hash}")
        print(f"✅ Admin wallet saved: {spending.admin_wallet}")
        
        # Double-check by querying database again
        verification = DonationSpending.objects.get(id=spending_id)
        print(f"🔍 Database verification - Status: {verification.blockchain_status}, TX: {verification.blockchain_tx_hash}")
        
        return JsonResponse({
            'success': True,
            'message': 'Spending recorded on blockchain successfully!',
            'tx_hash': tx_hash,
            'database_status': verification.blockchain_status
        })
        
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

def social_spending(request):
    """Dedicated social welfare spending management page"""
    # Handle login form submission
    if request.method == 'POST' and 'login' in request.POST:
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('/admin/spending/')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    # Check if user is authenticated and is admin
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        # Show login form instead of redirecting
        return render(request, 'donations/admin_login.html')
    
    donations = DonationTransaction.objects.all()
    spendings = DonationSpending.objects.all()
    
    # Calculate statistics
    total_donated_amount = sum(donation.amount for donation in donations)
    total_spent_amount = sum(spending.amount for spending in spendings)
    total_spendings = spendings.count()
    remaining_balance = total_donated_amount - total_spent_amount
    
    return render(request, 'donations/social_spending.html', {
        'spendings': spendings,
        'total_donated_amount': total_donated_amount,
        'total_spent_amount': total_spent_amount,
        'total_spendings': total_spendings,
        'remaining_balance': remaining_balance,
    })

def public_audit(request):
    """Public audit trail showing all recorded transactions and spendings"""
    recorded_donations = DonationTransaction.objects.filter(
        blockchain_status='recorded'
    ).exclude(blockchain_tx_hash__isnull=True)
    
    recorded_spendings = DonationSpending.objects.filter(
        blockchain_status='recorded'
    ).exclude(blockchain_tx_hash__isnull=True)
    
    # Calculate statistics
    total_verified_donations = recorded_donations.count()
    total_donated_amount = sum(donation.amount for donation in recorded_donations)
    
    total_verified_spendings = recorded_spendings.count()
    total_spent_amount = sum(spending.amount for spending in recorded_spendings)
    
    remaining_balance = total_donated_amount - total_spent_amount
    
    return render(request, 'donations/public_audit.html', {
        'donations': recorded_donations,
        'spendings': recorded_spendings,
        'total_verified_donations': total_verified_donations,
        'total_donated_amount': total_donated_amount,
        'total_verified_spendings': total_verified_spendings,
        'total_spent_amount': total_spent_amount,
        'remaining_balance': remaining_balance,
    })

def verified_donations(request):
    """Detailed view of all verified donations"""
    # Get all donations that are recorded on blockchain
    recorded_donations = DonationTransaction.objects.filter(blockchain_status='recorded').order_by('-created_at')
    
    # Calculate statistics
    total_verified_donations = recorded_donations.count()
    total_donated_amount = sum(donation.amount for donation in recorded_donations)
    recorded_donations_count = recorded_donations.count()
    
    return render(request, 'donations/verified_donations.html', {
        'donations': recorded_donations,
        'total_verified_donations': total_verified_donations,
        'total_donated_amount': total_donated_amount,
        'recorded_donations_count': recorded_donations_count,
    })

def donation_management(request):
    """Dedicated donation management page"""
    # Handle login form submission
    if request.method == 'POST' and 'login' in request.POST:
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('/admin/donations/')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    # Check if user is authenticated and is admin
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        # Show login form instead of redirecting
        return render(request, 'donations/admin_login.html')
    
    donations = DonationTransaction.objects.all()
    spendings = DonationSpending.objects.all()
    
    # Calculate donation statistics
    total_donations = donations.count()
    recorded_donations_count = donations.filter(blockchain_status='recorded').count()
    
    # Separate pending transactions: truly pending vs timed out
    all_pending = donations.filter(blockchain_status='pending')
    pending_donations_count = all_pending.filter(attempted_tx_hash__isnull=True).count()  # Never attempted
    timedout_donations_count = all_pending.exclude(attempted_tx_hash__isnull=True).exclude(attempted_tx_hash='').count()  # Has tx_hash but still pending
    
    total_donated_amount = sum(donation.amount for donation in donations)
    
    # Calculate spending statistics for available balance
    total_spent_amount = sum(spending.amount for spending in spendings)
    remaining_balance = total_donated_amount - total_spent_amount
    
    return render(request, 'donations/donation_management.html', {
        'donations': donations,
        'total_donations': total_donations,
        'recorded_donations_count': recorded_donations_count,
        'pending_donations_count': pending_donations_count,
        'timedout_donations_count': timedout_donations_count,
        'total_donated_amount': total_donated_amount,
        'total_spent_amount': total_spent_amount,
        'remaining_balance': remaining_balance,
    })

def verified_spending(request):
    """Detailed view of all verified social welfare spending"""
    # Get all spending that are recorded on blockchain
    recorded_spendings = DonationSpending.objects.filter(blockchain_status='recorded').order_by('-spent_date')
    
    # Calculate statistics
    total_verified_spendings = recorded_spendings.count()
    total_spent_amount = sum(spending.amount for spending in recorded_spendings)
    recorded_spendings_count = recorded_spendings.count()
    
    return render(request, 'donations/verified_spending.html', {
        'spendings': recorded_spendings,
        'total_verified_spendings': total_verified_spendings,
        'total_spent_amount': total_spent_amount,
        'recorded_spendings_count': recorded_spendings_count,
    })

@csrf_exempt
@require_http_methods(["POST"])
def verify_pending_transactions(request):
    """🚀 NEW: Manually verify pending blockchain transactions"""
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        from web3 import Web3
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Find pending donations with attempted transaction hashes
        pending_donations = DonationTransaction.objects.filter(
            blockchain_status='pending',
            attempted_tx_hash__isnull=False
        ).exclude(attempted_tx_hash='')
        
        if not pending_donations.exists():
            return JsonResponse({
                'success': True, 
                'message': 'No pending transactions to verify',
                'updated_count': 0
            })
        
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
                    break
            except Exception:
                continue
        
        if not w3:
            return JsonResponse({'success': False, 'error': 'Could not connect to Sepolia network'})
        
        updated_count = 0
        results = []
        
        for donation in pending_donations:
            try:
                receipt = w3.eth.get_transaction_receipt(donation.attempted_tx_hash)
                
                if receipt and receipt['status'] == 1:
                    # Transaction succeeded
                    donation.blockchain_status = 'recorded'
                    donation.blockchain_tx_hash = donation.attempted_tx_hash
                    donation.save()
                    updated_count += 1
                    
                    results.append({
                        'donor': donation.donor_name,
                        'status': 'success',
                        'tx_hash': donation.attempted_tx_hash
                    })
                elif receipt and receipt['status'] == 0:
                    # Transaction failed - keep as pending for retry
                    results.append({
                        'donor': donation.donor_name,
                        'status': 'failed_but_pending',
                        'tx_hash': donation.attempted_tx_hash,
                        'message': 'Transaction failed on blockchain, keeping as pending for retry'
                    })
                    # Don't change status - keep as 'pending' so it can be retried
                    
            except Exception as e:
                results.append({
                    'donor': donation.donor_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'message': f'Verification complete. Updated {updated_count} donations.',
            'updated_count': updated_count,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error verifying transactions: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def auto_record_pending(request):
    """🚀 NEW: Automatically record pending transactions on blockchain"""
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        # Check if auto-recording is enabled
        settings = AutoRecordingSettings.get_settings()
        if not settings.is_automatic_mode:
            return JsonResponse({
                'success': False, 
                'error': 'Auto-recording is disabled. Please enable automatic mode first.'
            })
        
        if not settings.credentials_configured:
            return JsonResponse({
                'success': False, 
                'error': 'No credentials configured for auto-recording.'
            })
        
        # Check if credentials exist
        if not credential_manager.credentials_exist():
            return JsonResponse({
                'success': False, 
                'error': 'No encrypted credentials found.'
            })
        
        # Initialize auto-recorder if not already done
        if not auto_recorder.is_initialized:
            if not auto_recorder.auto_initialize():
                return JsonResponse({
                    'success': False, 
                    'error': 'Could not initialize auto-recorder. Please toggle auto-mode again.'
                })
        
        # Find pending donations (last 24 hours)
        from datetime import timedelta
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        pending_donations = DonationTransaction.objects.filter(
            blockchain_status='pending',
            created_at__gte=cutoff_time
        ).order_by('created_at')
        
        if not pending_donations.exists():
            return JsonResponse({
                'success': True,
                'message': 'No pending donations found. All caught up!',
                'recorded_count': 0,
                'total_processed': 0,
                'results': []
            })
        
        recorded_count = 0
        failed_count = 0
        results = []
        
        for donation in pending_donations:
            try:
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
                        status = 'sent_pending'
                        message = f"Sent to blockchain (pending confirmation)"
                    else:
                        # Receipt received successfully
                        donation.blockchain_status = 'recorded'
                        donation.blockchain_tx_hash = result.get('tx_hash')
                        recorded_count += 1
                        status = 'recorded'
                        message = f"Successfully recorded on blockchain"
                    
                    # Update admin wallet and save
                    donation.admin_wallet = auto_recorder.account.address if auto_recorder.account else None
                    donation.save()
                    
                    results.append({
                        'donation_id': str(donation.id),
                        'donor_name': donation.donor_name,
                        'amount': str(donation.amount),
                        'status': status,
                        'tx_hash': result.get('tx_hash'),
                        'message': message
                    })
                    
                else:
                    failed_count += 1
                    error_msg = result.get('error', 'Unknown error')
                    
                    results.append({
                        'donation_id': str(donation.id),
                        'donor_name': donation.donor_name,
                        'amount': str(donation.amount),
                        'status': 'failed',
                        'error': error_msg,
                        'message': f"Failed to record: {error_msg}"
                    })
                    
            except Exception as e:
                failed_count += 1
                results.append({
                    'donation_id': str(donation.id),
                    'donor_name': donation.donor_name,
                    'amount': str(donation.amount),
                    'status': 'error',
                    'error': str(e),
                    'message': f"Exception: {str(e)}"
                })
                logger.error(f"Error auto-recording donation {donation.id}: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'Scan complete. Processed {pending_donations.count()} donations.',
            'total_processed': pending_donations.count(),
            'recorded_count': recorded_count,
            'pending_count': pending_donations.count() - recorded_count - failed_count,
            'failed_count': failed_count,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in auto_record_pending: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


# ===== NEW USER AUTHENTICATION & DASHBOARD VIEWS =====

def user_register(request):
    """User registration view"""
    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Welcome to CognizantTrust! Your account has been created successfully.')
            return redirect('donations:user_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DonorRegistrationForm()
    
    return render(request, 'donations/user_register.html', {'form': form})

def user_login(request):
    """Donor login view - redirects to user dashboard"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Try to authenticate with username or email
            user = authenticate(request, username=username, password=password)
            if not user:
                # Try with email
                try:
                    from django.contrib.auth.models import User
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user:
                # Check if user is admin trying to login via donor login
                if user.is_staff or user.is_superuser:
                    messages.error(request, 'Admin users should use the Admin Login. Redirecting you...')
                    return redirect('donations:admin_dashboard')
                
                auth_login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                next_url = request.GET.get('next', 'donations:user_dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'donations/user_login.html', {'form': form})

def user_logout(request):
    """User logout view"""
    user_name = request.user.get_full_name() or request.user.username if request.user.is_authenticated else "User"
    auth_logout(request)
    messages.success(request, f'Goodbye {user_name}! You have been logged out successfully.')
    return redirect('donations:home')

@login_required
def user_dashboard(request):
    """User dashboard showing donation history and profile"""
    # Check for donation success message
    donation_success_id = request.GET.get('donation_success')
    if donation_success_id:
        try:
            successful_donation = DonationTransaction.objects.get(
                id=donation_success_id, 
                donor=request.user
            )
            messages.success(
                request, 
                f'🎉 Your donation of ₹{successful_donation.amount} has been successfully processed! '
                f'Receipt #{successful_donation.receipt_number} has been generated.'
            )
        except DonationTransaction.DoesNotExist:
            pass
    
    # Get or create donor profile
    try:
        donor_profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        # Create profile for existing users who registered before the profile system
        donor_profile = DonorProfile.objects.create(
            user=request.user,
            phone_number="",
            address="",
            city="",
            state="",
            pincode=""
        )
    
    # Get user's donations
    user_donations = DonationTransaction.objects.filter(donor=request.user).order_by('-timestamp')
    
    # Calculate statistics
    total_donated = sum(donation.amount for donation in user_donations)
    donation_count = user_donations.count()
    recorded_donations = user_donations.filter(blockchain_status='recorded').count()
    pending_donations = user_donations.filter(blockchain_status='pending').count()
    
    # Get recent spending to show how trust uses donations
    recent_spending = DonationSpending.objects.filter(
        blockchain_status='recorded'
    ).order_by('-spent_date')[:5]
    
    context = {
        'donor_profile': donor_profile,
        'user_donations': user_donations[:10],  # Show recent 10
        'total_donated': total_donated,
        'donation_count': donation_count,
        'recorded_donations': recorded_donations,
        'pending_donations': pending_donations,
        'recent_spending': recent_spending,
    }
    
    return render(request, 'donations/user_dashboard.html', context)

@login_required
def user_donate(request):
    """Donation form for logged-in users"""
    if request.method == 'POST':
        form = UserDonationForm(request.POST)
        if form.is_valid():
            # Create donation linked to user
            donation = DonationTransaction.objects.create(
                donor=request.user,
                donor_name=request.user.get_full_name() or request.user.username,
                donor_email=request.user.email,
                donor_phone=getattr(request.user.donor_profile, 'phone_number', ''),
                amount=form.cleaned_data['amount'],
                purpose=form.cleaned_data['purpose'],
                upi_ref_id=f"UPI{uuid.uuid4().hex[:8].upper()}",
                blockchain_status='pending'
            )
            
            # Try auto-recording if enabled
            settings = AutoRecordingSettings.get_settings()
            if settings.is_automatic_mode:
                try:
                    from .auto_scanner import scan_and_record_pending
                    scan_result = scan_and_record_pending(max_age_hours=1, max_transactions=5)
                    logger.info(f"Auto-scan result after donation: {scan_result}")
                except Exception as e:
                    logger.error(f"Auto-scan error: {e}")
            
            messages.success(request, f'Thank you for your donation of ₹{donation.amount}! Your donation is being processed.')
            return redirect('donations:user_dashboard')
    else:
        form = UserDonationForm()
    
    return render(request, 'donations/user_donate.html', {'form': form})

@require_http_methods(["POST"])
def process_donation_ajax(request):
    """
    AJAX endpoint for real-time donation processing with actual backend steps
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    from django.db import transaction
    
    try:
        data = json.loads(request.body)
        amount = data.get('amount')
        purpose = data.get('purpose')
        
        # Validate input
        if not amount or not purpose:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValueError("Amount must be positive")
            if amount_decimal > 100000:  # Max donation limit
                raise ValueError("Amount exceeds maximum donation limit of ₹1,00,000")
        except (ValueError, decimal.InvalidOperation):
            return JsonResponse({'success': False, 'error': 'Invalid amount format'})
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
        # Test failure simulations (remove these in production)
        if purpose.lower().strip() == 'test error':
            return JsonResponse({
                'success': False, 
                'error': 'Test error simulation - donation processing failed'
            })
        elif purpose.lower().strip() == 'test payment failure':
            return JsonResponse({
                'success': False, 
                'error': 'Payment method declined - please try a different payment method'
            })
        elif purpose.lower().strip() == 'test system error':
            raise Exception("Simulated system error for testing")
        
        # Step 1: Validate donation details
        time.sleep(0.5)  # Simulate validation time
        
        # Check user profile completeness
        try:
            donor_profile = request.user.donor_profile
            if not donor_profile.phone_number or not donor_profile.address:
                return JsonResponse({
                    'success': False, 
                    'error': 'Please complete your profile before making donations',
                    'redirect': '/profile/'
                })
        except DonorProfile.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Please complete your profile before making donations',
                'redirect': '/profile/'
            })
        
        # Simulate processing steps
        time.sleep(0.7)  # Step 2 simulation
        time.sleep(0.8)  # Step 3 simulation
        time.sleep(0.6)  # Step 4 simulation
        
        # Check if auto-recording is available BEFORE creating donation
        from web3_integration.auto_recorder import auto_recorder
        auto_available = auto_recorder.is_initialized
        logger.info(f"🔍 Pre-donation check: auto_recorder.is_initialized = {auto_available}")
        
        # Note: We allow donations even if auto-recording is not available
        # Admin can manually record them on blockchain later
        
        # Only create donation if blockchain recording will work
        with transaction.atomic():
            # Generate unique UPI reference ID
            max_retries = 5
            for attempt in range(max_retries):
                upi_ref_id = f"UPI{uuid.uuid4().hex[:8].upper()}"
                
                try:
                    # Create donation transaction
                    donation = DonationTransaction.objects.create(
                        donor=request.user,
                        donor_name=request.user.get_full_name() or request.user.username,
                        donor_email=request.user.email,
                        donor_phone=donor_profile.phone_number,
                        amount=amount_decimal,
                        purpose=purpose,
                        upi_ref_id=upi_ref_id,
                        blockchain_status='pending'
                    )
                    break  # Success, exit retry loop
                    
                except IntegrityError as e:
                    if 'upi_ref_id' in str(e) and attempt < max_retries - 1:
                        # UPI ID collision, try again with new ID
                        continue
                    else:
                        # Other integrity error or max retries reached
                        raise
            
            # Generate receipt number
            if not donation.receipt_number:
                donation.save()  # This triggers receipt number generation
            
            # Log donation creation
            logger.info(f"🎉 New donation created: {donation.id} - {donation.donor_name} - ₹{donation.amount}")
            
            # Try auto-recording if available
            if auto_available:
                logger.info(f"🤖 Auto-recorder is available, attempting auto-scan for donation {donation.id}")
                try:
                    from donations.auto_scanner import scan_and_record_pending
                    logger.info(f"📞 Calling scan_and_record_pending for donation {donation.id}")
                    result = scan_and_record_pending(max_age_hours=0.1, max_transactions=5)
                    logger.info(f"✅ Auto-recording result for donation {donation.id}: {result}")
                except Exception as e:
                    logger.error(f"❌ Auto-recording failed for donation {donation.id}: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
            else:
                logger.info(f"ℹ️ Auto-recorder not available for donation {donation.id} - auto_available={auto_available}")
                    
            # Set realistic status message based on what actually happened
            if auto_available:
                status_message = "🎉 Your donation has been successfully processed! It is now being recorded on the Ethereum blockchain for permanent transparency and verification."
            else:
                status_message = "✅ Your donation has been successfully received! Our admin team will record it on the blockchain for transparency and verification."
        
        return JsonResponse({
            'success': True,
            'donation_id': str(donation.id),
            'receipt_number': donation.receipt_number,
            'amount': str(donation.amount),
            'message': status_message
        })
        
    except Exception as e:
        logger.error(f"Error processing donation via AJAX: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing your donation. Please try again.'
        })

def yield_progress(data):
    """Helper function to simulate progress updates - in real implementation this would use WebSockets or Server-Sent Events"""
    pass


@require_http_methods(["GET"])
@login_required
def get_donation_status(request, donation_id):
    """API endpoint to get real-time donation status"""
    try:
        donation = DonationTransaction.objects.get(id=donation_id, donor=request.user)
        
        # Determine display status
        if donation.blockchain_status == 'recorded':
            status = 'completed'
            status_text = 'Successfully Recorded on Blockchain'
            status_icon = 'fas fa-check-circle'
            status_color = 'success'
            details = {
                'message': f'🎉 Your donation has been permanently recorded on the Ethereum blockchain!',
                'tx_hash': donation.blockchain_tx_hash,
                'etherscan_url': f'https://sepolia.etherscan.io/tx/{"0x" if not donation.blockchain_tx_hash.startswith("0x") else ""}{donation.blockchain_tx_hash}' if donation.blockchain_tx_hash else None,
                'block_info': 'Transaction confirmed and immutable'
            }
        elif donation.blockchain_status == 'pending' and donation.attempted_tx_hash:
            status = 'processing'
            status_text = 'Confirming on Blockchain'
            status_icon = 'fas fa-sync fa-spin'
            status_color = 'warning'
            details = {
                'message': '⏳ Transaction sent to blockchain, waiting for confirmation...',
                'tx_hash': donation.attempted_tx_hash,
                'etherscan_url': f'https://sepolia.etherscan.io/tx/{"0x" if not donation.attempted_tx_hash.startswith("0x") else ""}{donation.attempted_tx_hash}',
                'block_info': 'Usually takes 15-30 seconds for confirmation'
            }
        elif donation.blockchain_status == 'pending':
            status = 'queued'
            status_text = 'Queued for Processing'
            status_icon = 'fas fa-clock'
            status_color = 'info'
            details = {
                'message': '📋 Your donation is queued for blockchain recording',
                'tx_hash': None,
                'etherscan_url': None,
                'block_info': 'Processing will begin shortly'
            }
        else:
            # Any other status should be treated as pending
            status = 'queued'
            status_text = 'Queued for Processing'
            status_icon = 'fas fa-clock'
            status_color = 'info'
            details = {
                'message': '📋 Your donation is queued for blockchain recording',
                'tx_hash': None,
                'etherscan_url': None,
                'block_info': 'Processing will retry automatically'
            }
        
        return JsonResponse({
            'success': True,
            'donation_id': str(donation.id),
            'status': status,
            'status_text': status_text,
            'status_icon': status_icon,
            'status_color': status_color,
            'blockchain_status': donation.blockchain_status,
            'amount': str(donation.amount),
            'purpose': donation.purpose,
            'created_at': donation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'details': details
        })
        
    except DonationTransaction.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Donation not found'})
    except Exception as e:
        logger.error(f"❌ Get donation status error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Server error'})


@login_required
def user_profile(request):
    """User profile editing view"""
    try:
        donor_profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        donor_profile = DonorProfile.objects.create(
            user=request.user,
            phone_number="",
            address="",
            city="",
            state="",
            pincode=""
        )
    
    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=donor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('donations:user_dashboard')
    else:
        form = DonorProfileForm(instance=donor_profile)
    
    return render(request, 'donations/user_profile.html', {
        'form': form,
        'donor_profile': donor_profile
    })

@login_required
def download_receipt(request, donation_id):
    """Download PDF receipt for a donation"""
    try:
        donation = get_object_or_404(DonationTransaction, id=donation_id, donor=request.user)
        
        # Import PDF generator
        from .pdf_generator import generate_donation_receipt
        from django.http import HttpResponse
        import logging
        
        # Generate PDF receipt
        pdf_data = generate_donation_receipt(donation)
        
        # Create HTTP response with PDF content type
        response = HttpResponse(pdf_data, content_type='application/pdf')
        
        # Set filename with receipt number or donation ID
        filename = f"cognizant_trust_receipt_{donation.receipt_number or str(donation.id)[:8]}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Mark receipt as generated if not already
        if not donation.receipt_generated:
            donation.receipt_generated = True
            donation.save(update_fields=['receipt_generated'])
        
        return response
        
    except Exception as e:
        # Log the error and return a user-friendly message
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating PDF receipt for donation {donation_id}: {str(e)}")
        messages.error(request, 'Unable to generate receipt. Please try again.')
        return redirect('donations:user_dashboard')

def spending_transparency(request):
    """Public view showing how trust uses donations"""
    spending_records = DonationSpending.objects.filter(
        blockchain_status='recorded'
    ).order_by('-spent_date')
    
    # Calculate spending by category
    from django.db.models import Sum
    spending_by_category = {}
    for category, display_name in DonationSpending.WELFARE_CATEGORIES:
        total = spending_records.filter(category=category).aggregate(Sum('amount'))['amount__sum'] or 0
        if total > 0:
            spending_by_category[display_name] = total
    
    # Calculate total donations vs spending
    total_donations = sum(d.amount for d in DonationTransaction.objects.filter(blockchain_status='recorded'))
    total_spending = sum(s.amount for s in spending_records)
    available_funds = total_donations - total_spending
    
    context = {
        'spending_records': spending_records[:20],  # Show recent 20
        'spending_by_category': spending_by_category,
        'total_donations': total_donations,
        'total_spending': total_spending,
        'available_funds': available_funds,
        'transparency_percentage': (total_spending / total_donations * 100) if total_donations > 0 else 0,
    }
    
    return render(request, 'donations/spending_transparency.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def toggle_background_processor(request):
    """Toggle background processor based on auto mode setting"""
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    try:
        from .background_processor import background_processor, start_background_processor, stop_background_processor
        
        # Get current auto mode setting
        settings = AutoRecordingSettings.get_settings()
        
        if settings.is_automatic_mode:
            # Start background processor
            if not background_processor.running:
                start_background_processor()
                logger.info("🚀 Background processor started via admin toggle")
                return JsonResponse({
                    'success': True,
                    'message': 'Background processor started - auto mode active',
                    'processor_running': True
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': 'Background processor already running',
                    'processor_running': True
                })
        else:
            # Stop background processor
            if background_processor.running:
                stop_background_processor()
                logger.info("⏹️ Background processor stopped via admin toggle")
                return JsonResponse({
                    'success': True,
                    'message': 'Background processor stopped - auto mode disabled',
                    'processor_running': False
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': 'Background processor already stopped',
                    'processor_running': False
                })
                
    except Exception as e:
        logger.error(f"Error toggling background processor: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def thread_monitor(request):
    """Detailed thread monitoring page for auto mode"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
    
    # Check if auto mode is enabled
    settings = AutoRecordingSettings.get_settings()
    if not settings.is_automatic_mode:
        messages.warning(request, "Thread monitoring is only available when auto mode is enabled.")
        return redirect('admin_dashboard')
    
    # Get detailed status from background processor
    try:
        from .background_processor import background_processor
        detailed_status = background_processor.get_detailed_status()
    except Exception as e:
        logger.error(f"Error getting detailed status: {e}")
        detailed_status = {'success': False, 'error': str(e)}
    
    context = {
        'detailed_status': detailed_status,
        'page_title': 'Thread Monitor',
        'refresh_interval': 10  # Auto-refresh every 10 seconds
    }
    
    return render(request, 'donations/thread_monitor.html', context)

@csrf_exempt
@require_http_methods(["GET"])
def get_detailed_processor_status(request):
    """API endpoint for detailed thread monitoring data"""
    try:
        from .background_processor import background_processor
        detailed_status = background_processor.get_detailed_status()
        return JsonResponse(detailed_status)
    except Exception as e:
        logger.error(f"Error getting detailed processor status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def get_processor_status(request):
    """API endpoint for basic processor status (existing compatibility)"""
    try:
        from .background_processor import background_processor
        status = background_processor.get_status()
        return JsonResponse(status)
    except Exception as e:
        logger.error(f"Error getting processor status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["GET"])
def debug_template_check(request):
    """Debug view to check if template updates are working"""
    try:
        from django.template.loader import get_template
        template = get_template('donations/admin_dashboard.html')
        
        # Check if our test badge is in the template
        with open('templates/donations/admin_dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        has_test_badge = 'TEMPLATE UPDATED!' in content
        has_background_threads = 'Background Threads:' in content
        
        return JsonResponse({
            'success': True,
            'template_has_test_badge': has_test_badge,
            'template_has_background_threads': has_background_threads,
            'file_size': len(content),
            'snippet': content[content.find('Blockchain Recording Mode'):content.find('Blockchain Recording Mode')+200] if 'Blockchain Recording Mode' in content else 'NOT FOUND'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
