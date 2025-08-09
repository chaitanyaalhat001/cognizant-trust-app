#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cognizanttrust.settings')
django.setup()

from django.contrib.auth.models import User
from donations.models import DonationTransaction

def create_sample_data():
    """Create sample donation data for demonstration"""
    
    # Set admin password
    try:
        admin = User.objects.get(username='admin')
        admin.set_password('admin123')  # Set a simple password for demo
        admin.save()
        print("✅ Admin password set to 'admin123'")
    except User.DoesNotExist:
        print("❌ Admin user not found")
    
    # Sample donation data
    sample_donations = [
        {
            'donor_name': 'Rahul Sharma',
            'amount': Decimal('1000.00'),
            'purpose': 'Education Aid for underprivileged children',
            'upi_ref_id': 'UPI12345678',
            'blockchain_status': 'pending',
            'timestamp': datetime.now() - timedelta(hours=2)
        },
        {
            'donor_name': 'Priya Patel',
            'amount': Decimal('2500.00'),
            'purpose': 'Medical treatment support for rural communities',
            'upi_ref_id': 'UPI87654321',
            'blockchain_status': 'recorded',
            'blockchain_tx_hash': '0x742d35cc6aa9c27aa167a64a32bbb42a4bfbba6b123456789abcdef0123456789',
            'admin_wallet': '0x742d35Cc5Aa9C27Aa167A64A32bbB42a4BFbBa6b',
            'timestamp': datetime.now() - timedelta(hours=5)
        },
        {
            'donor_name': 'Amit Kumar',
            'amount': Decimal('500.00'),
            'purpose': 'Food distribution program for homeless people',
            'upi_ref_id': 'UPI55555555',
            'blockchain_status': 'pending',
            'timestamp': datetime.now() - timedelta(minutes=30)
        },
        {
            'donor_name': 'Sita Rani',
            'amount': Decimal('1500.00'),
            'purpose': 'Clean water initiative for tribal areas',
            'upi_ref_id': 'UPI99999999',
            'blockchain_status': 'recorded',
            'blockchain_tx_hash': '0x123456789abcdef0742d35cc6aa9c27aa167a64a32bbb42a4bfbba6b987654321',
            'admin_wallet': '0x742d35Cc5Aa9C27Aa167A64A32bbB42a4BFbBa6b',
            'timestamp': datetime.now() - timedelta(days=1)
        },
        {
            'donor_name': 'Vikram Singh',
            'amount': Decimal('3000.00'),
            'purpose': 'Scholarship fund for engineering students',
            'upi_ref_id': 'UPI77777777',
            'blockchain_status': 'pending',
            'timestamp': datetime.now() - timedelta(minutes=15)
        }
    ]
    
    # Clear existing donations (for demo purposes)
    DonationTransaction.objects.all().delete()
    print("🗑️  Cleared existing donation data")
    
    # Create sample donations
    created_count = 0
    for donation_data in sample_donations:
        donation = DonationTransaction.objects.create(**donation_data)
        created_count += 1
        status_emoji = "✅" if donation.blockchain_status == 'recorded' else "⏳"
        print(f"{status_emoji} Created donation: {donation.donor_name} - ₹{donation.amount} - {donation.blockchain_status}")
    
    print(f"\n🎉 Successfully created {created_count} sample donations!")
    print(f"📊 Statistics:")
    print(f"   • Total donations: {DonationTransaction.objects.count()}")
    print(f"   • Recorded on blockchain: {DonationTransaction.objects.filter(blockchain_status='recorded').count()}")
    print(f"   • Pending recording: {DonationTransaction.objects.filter(blockchain_status='pending').count()}")
    print(f"   • Total amount: ₹{sum(d.amount for d in DonationTransaction.objects.all())}")

if __name__ == '__main__':
    create_sample_data() 