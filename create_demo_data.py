#!/usr/bin/env python
import os
import sys
import django
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cognizanttrust.settings')
django.setup()

from donations.models import DonationTransaction, DonationSpending

def create_sample_donations():
    """Create sample donation data to demonstrate real impact statistics"""
    
    # Sample donor data
    sample_donations = [
        {
            'donor_name': 'Rajesh Kumar',
            'amount': Decimal('5000'),
            'purpose': 'Education for underprivileged children',
            'blockchain_status': 'recorded',
            'days_ago': 1
        },
        {
            'donor_name': 'Priya Sharma',
            'amount': Decimal('10000'),
            'purpose': 'Healthcare for elderly',
            'blockchain_status': 'recorded',
            'days_ago': 3
        },
        {
            'donor_name': 'Amit Patel',
            'amount': Decimal('7500'),
            'purpose': 'Disaster relief operations',
            'blockchain_status': 'recorded',
            'days_ago': 5
        },
        {
            'donor_name': 'Sneha Reddy',
            'amount': Decimal('15000'),
            'purpose': 'Food distribution program',
            'blockchain_status': 'pending',
            'days_ago': 7
        },
        {
            'donor_name': 'Vikram Singh',
            'amount': Decimal('3000'),
            'purpose': 'School supplies for children',
            'blockchain_status': 'recorded',
            'days_ago': 10
        },
        {
            'donor_name': 'Anita Gupta',
            'amount': Decimal('25000'),
            'purpose': 'Medical equipment donation',
            'blockchain_status': 'recorded',
            'days_ago': 12
        },
        {
            'donor_name': 'Ravi Mehta',
            'amount': Decimal('8000'),
            'purpose': 'Rural education initiative',
            'blockchain_status': 'recorded',
            'days_ago': 15
        },
        {
            'donor_name': 'Kavitha Nair',
            'amount': Decimal('12000'),
            'purpose': 'Women empowerment program',
            'blockchain_status': 'recorded',
            'days_ago': 18
        },
        {
            'donor_name': 'Suresh Agarwal',
            'amount': Decimal('20000'),
            'purpose': 'Clean water project',
            'blockchain_status': 'recorded',
            'days_ago': 20
        },
        {
            'donor_name': 'Deepika Joshi',
            'amount': Decimal('6000'),
            'purpose': 'Elderly care support',
            'blockchain_status': 'pending',
            'days_ago': 22
        }
    ]
    
    # Create donation transactions
    created_count = 0
    for donation_data in sample_donations:
        # Check if donation already exists
        exists = DonationTransaction.objects.filter(
            donor_name=donation_data['donor_name'],
            amount=donation_data['amount']
        ).exists()
        
        if not exists:
            created_at = datetime.now() - timedelta(days=donation_data['days_ago'])
            
            donation = DonationTransaction.objects.create(
                donor_name=donation_data['donor_name'],
                amount=donation_data['amount'],
                purpose=donation_data['purpose'],
                blockchain_status=donation_data['blockchain_status'],
                upi_ref_id=f"UPI{uuid.uuid4().hex[:8].upper()}",
                timestamp=created_at
            )
            created_count += 1
            print(f"✅ Created donation: {donation.donor_name} - ₹{donation.amount}")
    
    print(f"\n🎉 Created {created_count} sample donations!")
    
    # Create some spending records to show impact
    sample_spending = [
        {
            'title': 'School Books and Supplies',
            'description': 'Purchased educational materials for underprivileged children',
            'category': 'education',
            'amount': Decimal('15000'),
            'beneficiaries': '50 children from rural schools',
            'location': 'Tamil Nadu villages',
            'blockchain_status': 'recorded',
            'days_ago': 2
        },
        {
            'title': 'Medical Supplies for Elderly',
            'description': 'Essential medicines and healthcare support for senior citizens',
            'category': 'healthcare',
            'amount': Decimal('25000'),
            'beneficiaries': '80 elderly individuals',
            'location': 'Mumbai care centers',
            'blockchain_status': 'recorded',
            'days_ago': 5
        },
        {
            'title': 'Food Distribution Drive',
            'description': 'Nutritious meal packets distributed to homeless population',
            'category': 'food_distribution',
            'amount': Decimal('18000'),
            'beneficiaries': '200 homeless individuals',
            'location': 'Delhi street communities',
            'blockchain_status': 'recorded',
            'days_ago': 8
        },
        {
            'title': 'Disaster Relief Operations',
            'description': 'Emergency supplies and shelter materials for flood victims',
            'category': 'disaster_relief',
            'amount': Decimal('22000'),
            'beneficiaries': '100 affected families',
            'location': 'Kerala flood zones',
            'blockchain_status': 'recorded',
            'days_ago': 12
        }
    ]
    
    spending_count = 0
    for spending_data in sample_spending:
        exists = DonationSpending.objects.filter(
            title=spending_data['title'],
            amount=spending_data['amount']
        ).exists()
        
        if not exists:
            spent_date = datetime.now() - timedelta(days=spending_data['days_ago'])
            
            spending = DonationSpending.objects.create(
                title=spending_data['title'],
                description=spending_data['description'],
                category=spending_data['category'],
                amount=spending_data['amount'],
                beneficiaries=spending_data['beneficiaries'],
                location=spending_data['location'],
                blockchain_status=spending_data['blockchain_status'],
                spent_date=spent_date
            )
            spending_count += 1
            print(f"✅ Created spending: {spending.title} - ₹{spending.amount}")
    
    print(f"\n🎉 Created {spending_count} sample spending records!")
    
    # Show summary statistics
    from django.db.models import Sum, Count
    
    total_donations = DonationTransaction.objects.filter(
        blockchain_status__in=['pending', 'recorded']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_donors = DonationTransaction.objects.filter(
        blockchain_status__in=['pending', 'recorded']
    ).values('donor_name').distinct().count()
    
    total_spending = DonationSpending.objects.filter(
        blockchain_status__in=['pending', 'recorded']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    lives_impacted = int(total_spending / 1000) if total_spending > 0 else 0
    
    print(f"\n📊 CURRENT IMPACT STATISTICS:")
    print(f"💰 Total Donations: ₹{total_donations:,.0f}")
    print(f"👥 Total Donors: {total_donors}")
    print(f"💝 Total Spending: ₹{total_spending:,.0f}")
    print(f"🌟 Lives Impacted: {lives_impacted}")
    print(f"\n🚀 Visit http://127.0.0.1:8000/ to see the updated statistics!")

if __name__ == "__main__":
    create_sample_donations() 