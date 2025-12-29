from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Wallet, WalletTransaction, BankAccount, Withdrawal
import random
import string


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    wallet_balance = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'profile_photo', 'wallet_balance',
            'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'role']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def generate_unique_username(self):
        """Generate a unique username"""
        while True:
            # Generate random username
            random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            username = f"user_{random_part}"
            if not User.objects.filter(username=username).exists():
                return username
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Generate unique username
        username = self.generate_unique_username()
        
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
            phone=validated_data.get('phone', ''),
            role=validated_data.get('role', 'customer')
        )
        
        # Create wallet for user
        Wallet.objects.create(user=user)
        
        return user


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for Wallet Transactions"""
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'transaction_type', 'amount', 'description',
            'related_booking', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for Bank Account"""
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'account_holder_name', 'account_number', 'ifsc_code',
            'bank_name', 'branch_name', 'is_primary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WithdrawalSerializer(serializers.ModelSerializer):
    """Serializer for Withdrawal"""
    bank_account = BankAccountSerializer(read_only=True)
    bank_account_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(),
        source='bank_account',
        write_only=True
    )
    
    class Meta:
        model = Withdrawal
        fields = [
            'id', 'bank_account', 'bank_account_id', 'amount', 'status',
            'transaction_id', 'notes', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'status', 'transaction_id', 'created_at', 'completed_at']
