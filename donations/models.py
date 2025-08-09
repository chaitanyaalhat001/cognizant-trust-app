from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import uuid

# Create your models here.

class DonorProfile(models.Model):
    """
    Extended profile for donors with essential information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    phone_number = models.CharField(
        max_length=15, 
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        help_text="Phone number for contact and UPI transactions"
    )
    address = models.TextField(help_text="Complete address for tax receipt purposes")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    pan_number = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        validators=[RegexValidator(regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message="Enter a valid PAN number in format: ABCDE1234F")],
        help_text="PAN number for tax exemption under 80G (optional)"
    )
    date_of_birth = models.DateField(blank=True, null=True, help_text="Date of birth for personalized communication")
    preferred_donation_causes = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Comma-separated list of preferred causes (e.g., education, healthcare, disaster relief)"
    )
    is_verified = models.BooleanField(default=False, help_text="Whether the donor profile is verified")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Donor Profile"
        verbose_name_plural = "Donor Profiles"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.phone_number}"
    
    @property
    def total_donations(self):
        """Get total amount donated by this user"""
        return sum(donation.amount for donation in self.user.donations.all())
    
    @property
    def total_donation_count(self):
        """Get total number of donations by this user"""
        return self.user.donations.count()
    
    @property
    def last_donation_date(self):
        """Get the date of last donation"""
        last_donation = self.user.donations.order_by('-timestamp').first()
        return last_donation.timestamp if last_donation else None


class DonationTransaction(models.Model):
    BLOCKCHAIN_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('recorded', 'Recorded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # NEW: Optional link to user account (for logged-in users)
    donor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='donations',
        help_text="Linked user account (if donated while logged in)"
    )
    # Keep original donor_name for backward compatibility and anonymous donations
    donor_name = models.CharField(max_length=255)
    donor_email = models.EmailField(blank=True, null=True, help_text="Email for receipt (if provided)")
    donor_phone = models.CharField(max_length=15, blank=True, null=True, help_text="Phone number (if provided)")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.TextField()
    upi_ref_id = models.CharField(max_length=50, unique=True)
    timestamp = models.DateTimeField(default=timezone.now)
    blockchain_status = models.CharField(
        max_length=20, 
        choices=BLOCKCHAIN_STATUS_CHOICES, 
        default='pending'
    )
    blockchain_tx_hash = models.CharField(max_length=66, blank=True, null=True)
    attempted_tx_hash = models.CharField(
        max_length=66, 
        blank=True, 
        null=True,
        help_text="Transaction hash from auto-recording attempt (even if receipt timed out)"
    )
    admin_wallet = models.CharField(max_length=42, blank=True, null=True)
    
    # NEW: Receipt generation fields
    receipt_generated = models.BooleanField(default=False, help_text="Whether receipt has been generated")
    receipt_number = models.CharField(max_length=50, blank=True, null=True, help_text="Unique receipt number")
    tax_exemption_claimed = models.BooleanField(default=False, help_text="Whether 80G tax exemption was claimed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.donor_name} - ₹{self.amount} - {self.purpose}"
    
    def save(self, *args, **kwargs):
        # Auto-generate receipt number if not exists
        if not self.receipt_number:
            self.receipt_number = f"CZT-{timezone.now().strftime('%Y%m%d')}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def is_recorded_on_blockchain(self):
        return self.blockchain_status == 'recorded' and self.blockchain_tx_hash
    
    @property
    def display_donor_name(self):
        """Get donor name from linked user or stored name"""
        if self.donor and self.donor.get_full_name():
            return self.donor.get_full_name()
        return self.donor_name
    
    @property
    def display_donor_email(self):
        """Get donor email from linked user or stored email"""
        if self.donor and self.donor.email:
            return self.donor.email
        return self.donor_email or "Not provided"


class DonationSpending(models.Model):
    BLOCKCHAIN_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('recorded', 'Recorded'),
    ]
    
    WELFARE_CATEGORIES = [
        ('education', 'Education'),
        ('healthcare', 'Healthcare'),
        ('food_distribution', 'Food Distribution'),
        ('shelter', 'Shelter & Housing'),
        ('disaster_relief', 'Disaster Relief'),
        ('elderly_care', 'Elderly Care'),
        ('child_welfare', 'Child Welfare'),
        ('skill_development', 'Skill Development'),
        ('sanitation', 'Sanitation & Hygiene'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, help_text="Brief title of the welfare activity")
    description = models.TextField(help_text="Detailed description of the expenditure")
    category = models.CharField(max_length=50, choices=WELFARE_CATEGORIES, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    beneficiaries = models.CharField(max_length=255, help_text="Who benefited from this spending")
    location = models.CharField(max_length=255, help_text="Location where the activity took place")
    spent_date = models.DateTimeField(default=timezone.now)
    blockchain_status = models.CharField(
        max_length=20, 
        choices=BLOCKCHAIN_STATUS_CHOICES, 
        default='pending'
    )
    blockchain_tx_hash = models.CharField(max_length=66, blank=True, null=True)
    admin_wallet = models.CharField(max_length=42, blank=True, null=True)
    receipt_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Receipt or bill reference number")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-spent_date']
        
    def __str__(self):
        return f"{self.title} - ₹{self.amount} - {self.get_category_display()}"
    
    @property
    def is_recorded_on_blockchain(self):
        return self.blockchain_status == 'recorded' and self.blockchain_tx_hash


class AutoRecordingSettings(models.Model):
    """
    Singleton model to store automatic recording settings.
    Only one instance should exist.
    """
    RECORDING_MODES = [
        ('manual', 'Manual (MetaMask Required)'),
        ('automatic', 'Automatic (Server-Side Signing)'),
    ]
    
    id = models.AutoField(primary_key=True)
    recording_mode = models.CharField(
        max_length=20, 
        choices=RECORDING_MODES, 
        default='manual',
        help_text="Choose between manual MetaMask approval or automatic server-side signing"
    )
    credentials_configured = models.BooleanField(
        default=False,
        help_text="Whether encrypted wallet credentials are stored"
    )
    last_auto_session = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Last time automatic recording was successfully used"
    )
    session_timeout_minutes = models.IntegerField(
        default=0,  # 0 means no timeout - permanent auto mode
        help_text="Auto-mode session timeout in minutes (0 = no timeout)"
    )
    max_auto_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=50000.00,
        help_text="Maximum amount that can be auto-recorded (safety limit)"
    )
    auto_recording_enabled = models.BooleanField(
        default=False,
        help_text="Master switch for automatic recording (additional safety)"
    )
    last_modified_by = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Admin user who last modified these settings"
    )
    security_audit_date = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Last security audit date"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Auto Recording Settings"
        verbose_name_plural = "Auto Recording Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        if not self.pk and AutoRecordingSettings.objects.exists():
            # Update existing instance instead of creating new one
            existing = AutoRecordingSettings.objects.first()
            existing.recording_mode = self.recording_mode
            existing.credentials_configured = self.credentials_configured
            existing.session_timeout_minutes = self.session_timeout_minutes
            existing.max_auto_amount = self.max_auto_amount
            existing.auto_recording_enabled = self.auto_recording_enabled
            existing.last_modified_by = self.last_modified_by
            existing.security_audit_date = self.security_audit_date
            existing.save()
            return existing
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'recording_mode': 'manual',
                'credentials_configured': False,
                'auto_recording_enabled': False,
            }
        )
        return settings
    
    def __str__(self):
        return f"Recording Mode: {self.get_recording_mode_display()}"
    
    @property
    def is_automatic_mode(self):
        return (self.recording_mode == 'automatic' and 
                self.credentials_configured and 
                self.auto_recording_enabled)
    
    @property
    def security_status(self):
        """Get security status for admin display"""
        if not self.credentials_configured:
            return "🔒 No Credentials Stored"
        elif not self.auto_recording_enabled:
            return "⏸️ Auto Recording Disabled"
        elif self.recording_mode == 'automatic':
            return "🤖 Automatic Mode Active"
        else:
            return "👤 Manual Mode Active"
