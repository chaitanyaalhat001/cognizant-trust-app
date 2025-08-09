# Generated manually to remove 'failed' status
from django.db import migrations, models

def convert_failed_to_pending(apps, schema_editor):
    """Convert any existing 'failed' status records to 'pending'"""
    DonationTransaction = apps.get_model('donations', 'DonationTransaction')
    DonationSpending = apps.get_model('donations', 'DonationSpending')
    
    # Update any failed donations to pending
    failed_donations = DonationTransaction.objects.filter(blockchain_status='failed')
    updated_donations = failed_donations.update(blockchain_status='pending')
    print(f"Updated {updated_donations} failed donation records to pending")
    
    # Update any failed spendings to pending  
    failed_spendings = DonationSpending.objects.filter(blockchain_status='failed')
    updated_spendings = failed_spendings.update(blockchain_status='pending')
    print(f"Updated {updated_spendings} failed spending records to pending")

def reverse_convert(apps, schema_editor):
    """Reverse operation - not needed since we're removing failed status"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0005_donationtransaction_donor_and_more'),
    ]

    operations = [
        migrations.RunPython(convert_failed_to_pending, reverse_convert),
        migrations.AlterField(
            model_name='donationtransaction',
            name='blockchain_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('recorded', 'Recorded')],
                default='pending',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='donationspending', 
            name='blockchain_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('recorded', 'Recorded')],
                default='pending',
                max_length=20
            ),
        ),
    ] 