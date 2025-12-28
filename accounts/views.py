from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import UserSerializer, UserRegistrationSerializer

User = get_user_model()


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Custom authentication class that doesn't enforce CSRF for mobile apps.
    """
    def enforce_csrf(self, request):
        # Override to bypass CSRF check for API calls
        pass  # Do not enforce CSRF for API calls


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user operations.
    CSRF exempt for mobile app API calls.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to exempt from CSRF.
        """
        return super().dispatch(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        User registration.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        User login - accepts either username or email.
        """
        username_or_email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        
        print(f"[LOGIN] Received data: username/email={username_or_email}, password length={len(password) if password else 0}")
        print(f"[LOGIN] Request data: {request.data}")
        
        if not username_or_email or not password:
            return Response(
                {'error': 'Username/Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Debug logging
        print(f"[LOGIN] Attempting authentication - Input: '{username_or_email}', Password length: {len(password)}")
        
        # Try to authenticate with username first
        user = authenticate(username=username_or_email, password=password)
        print(f"[LOGIN] Auth with username/email directly: {user is not None}")
        
        # If authentication failed, check if input is an email
        if user is None:
            # Check if the input looks like an email
            if '@' in username_or_email:
                print(f"[LOGIN] Input contains '@', trying email lookup...")
                try:
                    # Find user by email (case-insensitive)
                    user_by_email = User.objects.get(email__iexact=username_or_email)
                    print(f"[LOGIN] User found by email: {user_by_email.username}, email: {user_by_email.email}")
                    # Try to authenticate with the found username
                    user = authenticate(username=user_by_email.username, password=password)
                    print(f"[LOGIN] Auth with found username '{user_by_email.username}': {user is not None}")
                    if user is None:
                        print(f"[LOGIN] Password check failed for username: {user_by_email.username}")
                except User.DoesNotExist:
                    print(f"[LOGIN] User not found with email: {username_or_email}")
                    user = None
                except User.MultipleObjectsReturned:
                    print(f"[LOGIN] Multiple users found with email: {username_or_email}")
                    user_by_email = User.objects.filter(email__iexact=username_or_email).first()
                    if user_by_email:
                        user = authenticate(username=user_by_email.username, password=password)
                except Exception as e:
                    print(f"[LOGIN] Error during email lookup: {type(e).__name__}: {e}")
                    user = None
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Create session for the user
        login(request, user)
        print(f"[LOGIN] Session created for user: {user.username}")
        print(f"[LOGIN] Session key: {request.session.session_key}")
        
        # Check if provider and if they can login
        if user.role == 'provider':
            try:
                from providers.models import ServiceProvider
                provider = ServiceProvider.objects.get(user=user)
                
                # Check if onboarding is complete
                if not provider.is_onboarding_complete:
                    # Return 200 with onboarding info so session cookie is sent
                    return Response(
                        {
                            'user': UserSerializer(user).data,
                            'message': 'Please complete onboarding to continue.',
                            'onboarding_complete': False,
                            'verification_status': provider.verification_status,
                        },
                        status=status.HTTP_200_OK
                    )
                
                # Check if they can login (verification status)
                if not provider.can_login:
                    return Response(
                        {
                            'error': 'Your account is pending verification. Please wait for admin approval.',
                            'verification_status': provider.verification_status,
                            'onboarding_complete': provider.is_onboarding_complete
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ServiceProvider.DoesNotExist:
                # Provider profile doesn't exist, return 200 with onboarding info so session cookie is sent
                return Response(
                    {
                        'user': UserSerializer(user).data,
                        'message': 'Provider profile not found. Please complete onboarding.',
                        'onboarding_complete': False,
                    },
                    status=status.HTTP_200_OK
                )
        
        return Response({
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user information.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Update user profile.
        Supports password change and profile photo upload.
        """
        user = request.user
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # Handle password change if provided
        if 'current_password' in data and 'new_password' in data:
            current_password = data.pop('current_password')
            new_password = data.pop('new_password')
            
            # Verify current password
            if not user.check_password(current_password):
                return Response(
                    {'error': 'Current password is incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(new_password)
            user.save()
            print(f"✅ Password changed for user {user.username}")
        
        # Update other fields
        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            print(f"✅ Profile updated for user {user.username}: {data}")
            return Response(serializer.data)
        
        print(f"❌ Profile update validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
