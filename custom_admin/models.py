from django.db import models


class EmailSettings(models.Model):
    """
    Singleton-style settings for sending email (e.g. password reset).
    Only one row is used; configure via custom admin panel.
    """
    smtp_host = models.CharField(max_length=255, blank=True, help_text='e.g. smtp.gmail.com')
    smtp_port = models.PositiveIntegerField(default=587, help_text='Usually 587 (TLS) or 465 (SSL)')
    smtp_username = models.CharField(max_length=255, blank=True, help_text='SMTP login username/email')
    smtp_password = models.CharField(max_length=255, blank=True, help_text='SMTP password or app password')
    from_email = models.EmailField(blank=True, help_text='From address for outgoing emails')
    use_tls = models.BooleanField(default=True, help_text='Use TLS (recommended for port 587)')
    is_active = models.BooleanField(
        default=False,
        help_text='When enabled, password reset and other emails use these settings. When disabled, console backend is used.'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email settings'
        verbose_name_plural = 'Email settings'

    def __str__(self):
        return f'SMTP {self.smtp_host or "(not set)"}'

    def is_configured(self):
        """True if we have enough settings to send via SMTP."""
        return bool(
            self.is_active
            and self.smtp_host
            and self.from_email
            and self.smtp_username
            and self.smtp_password
        )
