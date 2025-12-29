from django.db import models
from django.conf import settings
from services.models import ServiceCategory


class ServiceProvider(models.Model):
    """Service Provider Profile"""
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_provider'
    )
    
    # Basic Information
    name = models.CharField(max_length=200, blank=True)
    contact = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='provider_photos/', null=True, blank=True)
    
    # Location Information (Screen 1)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_string = models.CharField(max_length=500, blank=True, help_text="Human-readable location address")
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    
    # Documents (Screen 3)
    pan_card = models.FileField(upload_to='documents/pan/', null=True, blank=True)
    registration_certificate = models.FileField(
        upload_to='documents/registration/',
        null=True,
        blank=True
    )
    
    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )
    verification_notes = models.TextField(blank=True, help_text="Admin notes for verification")
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_providers'
    )
    
    # Onboarding Status
    onboarding_step = models.IntegerField(default=1, help_text="Current onboarding step (1, 2, or 3)")
    is_onboarding_complete = models.BooleanField(default=False)
    
    # Availability Schedule
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    available_from_day = models.CharField(
        max_length=10,
        choices=DAY_CHOICES,
        null=True,
        blank=True,
        help_text="First day of availability (e.g., Monday)"
    )
    available_to_day = models.CharField(
        max_length=10,
        choices=DAY_CHOICES,
        null=True,
        blank=True,
        help_text="Last day of availability (e.g., Friday)"
    )
    available_start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time of availability (e.g., 09:00)"
    )
    available_end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="End time of availability (e.g., 17:00)"
    )
    
    # Pricing
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Minimum price the provider charges")
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum price the provider charges")
    
    @property
    def is_available(self):
        """Check if provider is currently available based on schedule"""
        from django.utils import timezone
        from datetime import datetime, time
        
        # If no schedule is set, consider as not available
        if not self.available_from_day or not self.available_to_day:
            return False
        
        if not self.available_start_time or not self.available_end_time:
            return False
        
        now = timezone.now()
        current_day = now.strftime('%A').lower()
        current_time = now.time()
        
        # Map day names to numbers for comparison
        day_map = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6,
        }
        
        current_day_num = day_map.get(current_day, -1)
        from_day_num = day_map.get(self.available_from_day, -1)
        to_day_num = day_map.get(self.available_to_day, -1)
        
        if current_day_num == -1 or from_day_num == -1 or to_day_num == -1:
            return False
        
        # Check if current day is within range
        if from_day_num <= to_day_num:
            # Normal range (e.g., Monday to Friday)
            day_in_range = from_day_num <= current_day_num <= to_day_num
        else:
            # Wrapping range (e.g., Friday to Monday)
            day_in_range = current_day_num >= from_day_num or current_day_num <= to_day_num
        
        if not day_in_range:
            return False
        
        # Check if current time is within range
        return self.available_start_time <= current_time <= self.available_end_time
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.verification_status}"
    
    @property
    def can_login(self):
        """Provider can only login if verified"""
        return self.verification_status == 'approved' and self.is_onboarding_complete


class ProviderService(models.Model):
    """Services that a provider offers (Screen 2)"""
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='services'
    )
    service_category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='providers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['provider', 'service_category']
        ordering = ['service_category__name']
    
    def __str__(self):
        return f"{self.provider.name} - {self.service_category.name}"


class ReferralCode(models.Model):
    """Referral codes for tracking"""
    code = models.CharField(max_length=50, unique=True)
    used_by = models.ForeignKey(
        ServiceProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_referral'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.code
