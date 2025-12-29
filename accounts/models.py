from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal


class User(AbstractUser):
    """Custom User model"""
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    fcm_token = models.TextField(null=True, blank=True, help_text="Firebase Cloud Messaging device token for push notifications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    @property
    def wallet_balance(self):
        """Get wallet balance for this user"""
        wallet, _ = Wallet.objects.get_or_create(user=self)
        return wallet.balance


class Wallet(models.Model):
    """User wallet for storing money"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current wallet balance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}'s Wallet - Rs. {self.balance}/-"
    
    def add_money(self, amount):
        """Add money to wallet"""
        self.balance += Decimal(str(amount))
        self.save()
        return self.balance
    
    def deduct_money(self, amount):
        """Deduct money from wallet"""
        if self.balance >= Decimal(str(amount)):
            self.balance -= Decimal(str(amount))
            self.save()
            return True
        return False


class WalletTransaction(models.Model):
    """Transaction history for wallet"""
    TRANSACTION_TYPES = [
        ('add_money', 'Add Money'),
        ('payment', 'Payment'),
        ('received', 'Received Payment'),
        ('withdrawal', 'Withdrawal'),
    ]
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    related_booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.user.username} - {self.get_transaction_type_display()} - Rs. {self.amount}/-"


class BankAccount(models.Model):
    """Bank account details for providers to receive payments"""
    provider = models.ForeignKey(
        'providers.ServiceProvider',
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    account_holder_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=11)
    bank_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False, help_text="Primary account for withdrawals")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
        unique_together = [['provider', 'account_number']]
    
    def __str__(self):
        return f"{self.provider.name} - {self.bank_name} ({self.account_number[-4:]})"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary accounts
        if self.is_primary:
            BankAccount.objects.filter(provider=self.provider, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Withdrawal(models.Model):
    """Withdrawal requests from provider wallet to bank account"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    provider = models.ForeignKey(
        'providers.ServiceProvider',
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Bank transaction ID")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider.name} - Rs. {self.amount}/- ({self.status})"
