from django.db import models
from django.conf import settings
from providers.models import ServiceProvider
from services.models import ServiceCategory


class Booking(models.Model):
    """Booking/Request model for service bookings"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('negotiation', 'Negotiation'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('payment', 'Payment'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    service_category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    description = models.TextField(blank=True, help_text="Service description/requirements")
    saved_address = models.ForeignKey(
        'addresses.SavedAddress',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='bookings',
        help_text="Service address from user's saved addresses",
    )
    address = models.TextField(blank=True, default='', help_text="Denormalized address text (from saved_address or legacy)")
    scheduled_date = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Currently proposed price during negotiation")
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='price_proposals',
        help_text="User who proposed the current price"
    )
    price_locked = models.BooleanField(default=False, help_text="Price is locked after acceptance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.username} - {self.provider.name} ({self.status})"

