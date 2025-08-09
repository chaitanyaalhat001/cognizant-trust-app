#!/usr/bin/env python3
"""
Create a timeout transaction for testing the Refresh Blockchain Status button
This script creates a donation record that appears to have timed out but is actually successful on blockchain
"""

import os
import sys
import django
from datetime import datetime
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cognizanttrust.settings')
django.setup()

from donations.models import DonationTransaction
from django.utils import timezone

def create_timeout_transaction():
    """Create a test transaction that appears to have timed out"""
    
    # Use the successful transaction hash from earlier
    successful_tx_hash = "dc4819514d801ed9686ffdc5b80817da57004eae598e550972d5412fe32ac27b"
    
    # Create a test donation that looks like it timed out
    test_donation = DonationTransaction.objects.create(
        donor_name="Test Timeout User",
        donor_email="timeout@test.com", 
        donor_phone="9999999999",
        amount=25.00,  # ₹25.00
        purpose="Testing timeout refresh functionality",
        upi_ref_id=f"TEST_TIMEOUT_{uuid.uuid4().hex[:8].upper()}",
        blockchain_status='pending',  # Still shows as pending
        attempted_tx_hash=successful_tx_hash,  # But has a successful tx hash
        timestamp=timezone.now(),
        created_at=timezone.now()
    )
    
    print("✅ Created timeout test transaction:")
    print(f"   📝 Donor: {test_donation.donor_name}")
    print(f"   💰 Amount: ₹{test_donation.amount}")
    print(f"   🔗 TX Hash: {test_donation.attempted_tx_hash}")
    print(f"   📊 Status: {test_donation.blockchain_status} (should update to 'recorded')")
    print(f"   🆔 ID: {test_donation.id}")
    print()
    print("🔧 Now test the 'Refresh Blockchain Status' button in admin dashboard!")
    print("   The button should update this transaction from 'pending' to 'recorded'")
    
    return test_donation

if __name__ == "__main__":
    try:
        donation = create_timeout_transaction()
        print(f"\n🎯 Test transaction created successfully with ID: {donation.id}")
    except Exception as e:
        print(f"❌ Error creating test transaction: {e}")
        sys.exit(1) 