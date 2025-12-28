from django.db import models
from django.conf import settings


class SavedAddress(models.Model):
    """Model for user saved addresses"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_addresses'
    )
    label = models.CharField(max_length=100, help_text="e.g., Home, Office, etc.")
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False, help_text="Default address for bookings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name_plural = 'Saved Addresses'

    def __str__(self):
        return f"{self.user.username} - {self.label}"

    def get_full_address(self):
        """Return formatted full address"""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.state, self.postal_code, self.country])
        return ', '.join(filter(None, parts))

    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            SavedAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
