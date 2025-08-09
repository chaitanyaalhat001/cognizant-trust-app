from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('', views.home, name='home'),
    path('submit/', views.submit_donation, name='submit_donation'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/donations/', views.donation_management, name='donation_management'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/record-blockchain/', views.record_on_blockchain, name='record_on_blockchain'),
    path('admin/update-status/', views.update_blockchain_status, name='update_blockchain_status'),
    path('admin/spending/', views.social_spending, name='social_spending'),
    path('admin/submit-spending/', views.submit_spending, name='submit_spending'),
    path('admin/record-spending-blockchain/', views.record_spending_on_blockchain, name='record_spending_on_blockchain'),
    
    # 🚀 NEW: Auto Recording Management APIs
    path('admin/store-credentials/', views.store_wallet_credentials, name='store_wallet_credentials'),
    path('admin/toggle-mode/', views.toggle_recording_mode, name='toggle_recording_mode'),
    path('admin/delete-credentials/', views.delete_credentials, name='delete_credentials'),
    path('admin/verify-pending/', views.verify_pending_transactions, name='verify_pending_transactions'),
    path('api/verify-pending-transactions/', views.verify_pending_transactions, name='api_verify_pending_transactions'),
    path('admin/auto-record-pending/', views.auto_record_pending, name='auto_record_pending'),

    
    # 🚀 NEW: Background Processor Management APIs
    path('admin/toggle-processor/', views.toggle_background_processor, name='toggle_background_processor'),
    path('admin/processor-status/', views.get_processor_status, name='get_processor_status'),
    path('debug/template-check/', views.debug_template_check, name='debug_template_check'),
    
            # 🚀 NEW: User Authentication & Dashboard URLs
        path('register/', views.user_register, name='user_register'),
        path('login/', views.user_login, name='user_login'),
        path('logout/', views.user_logout, name='user_logout'),
        path('dashboard/', views.user_dashboard, name='user_dashboard'),
        path('donate/', views.user_donate, name='user_donate'),
        path('api/process-donation/', views.process_donation_ajax, name='process_donation_ajax'),
    path('api/donation-status/<str:donation_id>/', views.get_donation_status, name='get_donation_status'),
        path('profile/', views.user_profile, name='user_profile'),
        path('receipt/<uuid:donation_id>/', views.download_receipt, name='download_receipt'),
        path('transparency/', views.spending_transparency, name='spending_transparency'),
    
    path('audit/', views.public_audit, name='public_audit'),
    path('audit/donations/', views.verified_donations, name='verified_donations'),
    path('audit/spending/', views.verified_spending, name='verified_spending'),
    path('admin/thread-monitor/', views.thread_monitor, name='thread_monitor'),
    path('api/detailed-processor-status/', views.get_detailed_processor_status, name='detailed_processor_status'),
] 