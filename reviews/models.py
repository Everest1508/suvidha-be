from django.db import models
from django.conf import settings
from providers.models import ServiceProvider


class Review(models.Model):
    """Review model for service provider reviews"""
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # Allow multiple reviews for different service categories from same provider
        # Also allow reviewing same service multiple times if booked multiple times
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'customer', 'service_category'],
                name='unique_review_per_service',
                condition=models.Q(service_category__isnull=False)
            ),
            # Allow one review per provider if service_category is null
            models.UniqueConstraint(
                fields=['provider', 'customer'],
                name='unique_review_per_provider_no_service',
                condition=models.Q(service_category__isnull=True)
            ),
        ]
    
    def __str__(self):
        return f"{self.customer.username} - {self.provider.name} ({self.rating} stars)"

