from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Notification model"""
    NOTIFICATION_TYPES = [
        ('booking_created', 'New Booking Request'),
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_accepted', 'Booking Accepted'),
        ('booking_completed', 'Booking Completed'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('service_completed', 'Service Completed'),
        ('payment_received', 'Payment Received'),
        ('new_provider', 'New Provider Available'),
        ('verification_approved', 'Verification Approved'),
        ('verification_rejected', 'Verification Rejected'),
        ('general', 'General'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='general'
    )
    is_read = models.BooleanField(default=False)
    related_id = models.IntegerField(null=True, blank=True, help_text="ID of related object (booking, service, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

