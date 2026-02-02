from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import authenticate, login
from django.core.cache import cache
from django.core.mail import send_mail, get_connection
import random
import string
from decimal import Decimal
from .models import User, Wallet, WalletTransaction, BankAccount, Withdrawal
from .serializers import (
    UserSerializer, UserRegistrationSerializer, WalletSerializer,
    WalletTransactionSerializer, BankAccountSerializer, WithdrawalSerializer
)
from providers.models import ServiceProvider


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Custom authentication class that doesn't enforce CSRF for mobile apps."""
    def enforce_csrf(self, request):
        pass


@method_decorator(csrf_exempt, name='dispatch')
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user operations"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user info"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def register(self, request):
        """Register a new user"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def login(self, request):
        """User login - accepts username or email"""
        username_or_email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        
        print(f"🔐 Login attempt - Username/Email: {username_or_email}")
        print(f"🔐 Password length: {len(password) if password else 0}")
        
        if not username_or_email or not password:
            return Response(
                {'error': 'Username/email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to authenticate with username first
        user = authenticate(username=username_or_email, password=password)
        print(f"🔐 Username authentication result: {user is not None}")
        
        # If that fails, try with email
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                print(f"🔐 Found user by email: {user_obj.username}")
                user = authenticate(username=user_obj.username, password=password)
                print(f"🔐 Email authentication result: {user is not None}")
            except User.DoesNotExist:
                print(f"🔐 No user found with email: {username_or_email}")
                user = None
            except User.MultipleObjectsReturned:
                print(f"🔐 Multiple users found with email: {username_or_email}")
                user_obj = User.objects.filter(email=username_or_email).first()
                if user_obj:
                    user = authenticate(username=user_obj.username, password=password)
        
        if user:
            print(f"🔐 User found: {user.username}, is_active: {user.is_active}")
            if user.is_active:
                login(request, user)
                print(f"🔐 Login successful for user: {user.username}")
                return Response(
                    UserSerializer(user).data,
                    status=status.HTTP_200_OK
                )
            else:
                print(f"🔐 User account is inactive")
                return Response(
                    {'error': 'Your account is inactive. Please contact support.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        print(f"🔐 Authentication failed - Invalid credentials")
        return Response(
            {'error': 'Invalid credentials. Please check your username/email and password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    @action(detail=False, methods=['post'], permission_classes=[])
    def forgot_password(self, request):
        """Send a 6-digit reset code to the user's email. No auth required."""
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether email exists
            return Response(
                {'success': True, 'message': 'If an account exists with this email, you will receive a code shortly.'},
                status=status.HTTP_200_OK
            )
        code = ''.join(random.choices(string.digits, k=6))
        cache_key = f'pw_reset:{email}'
        cache.set(cache_key, code, timeout=900)  # 15 minutes
        try:
            connection = None
            from_email = None
            try:
                from custom_admin.models import EmailSettings
                settings_obj = EmailSettings.objects.first()
                if settings_obj and settings_obj.is_configured():
                    connection = get_connection(
                        backend='django.core.mail.backends.smtp.EmailBackend',
                        host=settings_obj.smtp_host,
                        port=settings_obj.smtp_port,
                        username=settings_obj.smtp_username,
                        password=settings_obj.smtp_password,
                        use_tls=settings_obj.use_tls,
                        fail_silently=False,
                    )
                    from_email = settings_obj.from_email or settings_obj.smtp_username
                    print(f"📧 Sending password reset email via Custom Admin SMTP ({settings_obj.smtp_host})")
                else:
                    print("📧 Email Settings not configured or disabled – using default backend (email may only appear in console)")
            except Exception as e:
                print(f"📧 EmailSettings not available, using default backend: {e}")
            send_mail(
                subject='Your password reset code - Suvidha Connect',
                message=f'Your password reset code is: {code}\n\nThis code expires in 15 minutes.\n\nIf you did not request this, please ignore this email.',
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
                connection=connection,
            )
        except Exception as e:
            print(f"❌ Failed to send password reset email: {e}")
            cache.delete(cache_key)
            return Response(
                {'error': 'Failed to send email. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response(
            {'success': True, 'message': 'If an account exists with this email, you will receive a code shortly.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[])
    def reset_password(self, request):
        """Verify code and set new password. No auth required."""
        email = (request.data.get('email') or '').strip().lower()
        code = (request.data.get('code') or '').strip()
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not code:
            return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password:
            return Response({'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != new_password_confirm:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f'pw_reset:{email}'
        stored_code = cache.get(cache_key)
        if not stored_code or stored_code != code:
            return Response(
                {'error': 'Invalid or expired code. Please request a new code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid or expired code.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            msg = e.messages[0] if e.messages else 'Invalid password.'
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        cache.delete(cache_key)
        return Response(
            {'success': True, 'message': 'Password has been reset. You can now log in.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def register_fcm_token(self, request):
        """Register or update FCM device token for push notifications."""
        fcm_token = request.data.get('fcm_token')
        
        if not fcm_token:
            print("❌ FCM token is missing in the request.")
            return Response(
                {'error': 'fcm_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Basic validation for token length (FCM tokens are usually long)
        if len(fcm_token) < 50:
            print(f"❌ FCM token too short (length: {len(fcm_token)}). Possible invalid token.")
            return Response(
                {'error': 'Invalid FCM token format or length'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        user.fcm_token = fcm_token
        user.save()
        
        print(f"✅ FCM token registered for user {user.username}. Token length: {len(fcm_token)}, starts with: {fcm_token[:20]}...")
        
        return Response({
            'message': 'FCM token registered successfully',
            'fcm_token': user.fcm_token
        })
    
    @action(detail=False, methods=['patch', 'put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update user profile information."""
        user = request.user
        
        # Handle both JSON and form data
        if hasattr(request.data, 'copy'):
            data = request.data.copy()
        else:
            data = dict(request.data)
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        
        # Handle profile photo if provided (multipart form data)
        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
        
        try:
            user.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"❌ Error updating profile: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet for wallet operations"""
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get current wallet balance"""
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            'balance': float(wallet.balance),
            'wallet_id': wallet.id
        })
    
    @action(detail=False, methods=['post'])
    def add_money(self, request):
        """Add money to wallet (simulation)"""
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'simulation')
        
        if not amount:
            return Response(
                {'error': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return Response(
                    {'error': 'Amount must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        
        with transaction.atomic():
            wallet.add_money(amount_decimal)
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='add_money',
                amount=amount_decimal,
                description=f'Added money via {payment_method} (simulation)'
            )
        
        return Response({
            'success': True,
            'balance': float(wallet.balance),
            'message': f'Rs. {amount_decimal}/- added to wallet successfully'
        })
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get wallet transaction history"""
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        transactions = wallet.transactions.all()[:50]  # Last 50 transactions
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class BankAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for bank account management (providers only)"""
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]
    pagination_class = None  # Disable pagination for bank accounts
    
    def get_queryset(self):
        if self.request.user.role != 'provider':
            return BankAccount.objects.none()
        try:
            provider = ServiceProvider.objects.get(user=self.request.user)
            return BankAccount.objects.filter(provider=provider)
        except ServiceProvider.DoesNotExist:
            return BankAccount.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Override create to add better error handling"""
        if request.user.role != 'provider':
            return Response(
                {'detail': 'Only providers can add bank accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            provider = ServiceProvider.objects.get(user=request.user)
        except ServiceProvider.DoesNotExist:
            return Response(
                {'detail': 'Provider profile not found. Please complete your provider onboarding.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(provider=provider)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class WithdrawalViewSet(viewsets.ModelViewSet):
    """ViewSet for withdrawal requests (providers only)"""
    serializer_class = WithdrawalSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    def get_queryset(self):
        if self.request.user.role != 'provider':
            return Withdrawal.objects.none()
        try:
            provider = ServiceProvider.objects.get(user=self.request.user)
            return Withdrawal.objects.filter(provider=provider)
        except ServiceProvider.DoesNotExist:
            return Withdrawal.objects.none()
    
    def create(self, request):
        """Create withdrawal request"""
        if request.user.role != 'provider':
            return Response(
                {'error': 'Only providers can withdraw money'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            provider = ServiceProvider.objects.get(user=request.user)
        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Provider profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        amount = request.data.get('amount')
        bank_account_id = request.data.get('bank_account_id')
        
        if not amount or not bank_account_id:
            return Response(
                {'error': 'Amount and bank_account_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return Response(
                    {'error': 'Amount must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get provider's wallet
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        
        if wallet.balance < amount_decimal:
            return Response(
                {'error': 'Insufficient wallet balance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bank_account = BankAccount.objects.get(id=bank_account_id, provider=provider)
        except BankAccount.DoesNotExist:
            return Response(
                {'error': 'Bank account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create withdrawal (simulation - immediately complete it)
        with transaction.atomic():
            # Deduct from wallet
            wallet.deduct_money(amount_decimal)
            
            # Create withdrawal record
            withdrawal = Withdrawal.objects.create(
                provider=provider,
                bank_account=bank_account,
                amount=amount_decimal,
                status='completed',  # Simulation - immediately complete
                transaction_id=f'TXN{timezone.now().strftime("%Y%m%d%H%M%S")}{request.user.id}',
                notes='Simulated withdrawal',
                completed_at=timezone.now()
            )
            
            # Create transaction record
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='withdrawal',
                amount=amount_decimal,
                description=f'Withdrawal to {bank_account.bank_name} ({bank_account.account_number[-4:]})'
            )
        
        serializer = self.get_serializer(withdrawal)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
