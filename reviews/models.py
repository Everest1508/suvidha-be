from django.db import models
from django.conf import settings
from providers.models import ServiceProvider


class Review(models.Model):
    """Review model: one review per booking (booking-based). Same provider can be reviewed multiple times for different bookings."""
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    service_category = models.ForeignKey(
        'services.ServiceCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews'
    )
    # One review per completed booking; allows reviewing same provider again for different bookings
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        constraints = [
            # One review per booking when booking is set
            models.UniqueConstraint(
                fields=['booking'],
                name='unique_review_per_booking',
                condition=models.Q(booking__isnull=False)
            ),
        ]
    
    def __str__(self):
        return f"{self.customer.username} - {self.provider.name} ({self.rating} stars)"

