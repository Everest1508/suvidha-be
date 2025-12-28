from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import ServiceProvider, ProviderService, ReferralCode
from .serializers import (
    ServiceProviderSerializer,
    OnboardingStep1Serializer,
    OnboardingStep2Serializer,
    OnboardingStep3Serializer,
    ProviderRegistrationSerializer
)
from services.models import ServiceCategory

User = get_user_model()


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Custom authentication class that doesn't enforce CSRF for mobile apps.
    """
    def enforce_csrf(self, request):
        # Override to bypass CSRF check for API calls
        pass  # Do not enforce CSRF for API calls


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service provider operations including onboarding.
    CSRF exempt for mobile app API calls.
    """
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [AllowAny]  # Will be customized per action
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
        Complete provider registration with all onboarding steps.
        """
        serializer = ProviderRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            provider = serializer.save()
            return Response(
                ServiceProviderSerializer(provider).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def onboarding_step1(self, request):
        """
        Screen 1: Save location and referral code.
        """
        provider, created = ServiceProvider.objects.get_or_create(
            user=request.user,
            defaults={'name': request.user.username}
        )
        
        serializer = OnboardingStep1Serializer(data=request.data)
        if serializer.is_valid():
            provider.latitude = serializer.validated_data['latitude']
            provider.longitude = serializer.validated_data['longitude']
            provider.location_string = serializer.validated_data['location_string']
            provider.referral_code = serializer.validated_data.get('referral_code', '')
            provider.onboarding_step = 1
            provider.save()
            
            # Handle referral code
            if provider.referral_code:
                ReferralCode.objects.get_or_create(
                    code=provider.referral_code,
                    defaults={'used_by': provider}
                )
            
            return Response(
                {
                    'message': 'Step 1 completed successfully',
                    'onboarding_step': provider.onboarding_step,
                    'provider': ServiceProviderSerializer(provider).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def onboarding_step2(self, request):
        """
        Screen 2: Save selected services.
        """
        provider = get_object_or_404(ServiceProvider, user=request.user)
        
        serializer = OnboardingStep2Serializer(data=request.data)
        if serializer.is_valid():
            service_ids = serializer.validated_data['service_ids']
            
            # Validate service IDs exist
            valid_services = ServiceCategory.objects.filter(
                id__in=service_ids,
                is_active=True
            )
            if valid_services.count() != len(service_ids):
                return Response(
                    {'error': 'Some service IDs are invalid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Clear existing services and add new ones
            ProviderService.objects.filter(provider=provider).delete()
            for service in valid_services:
                ProviderService.objects.create(
                    provider=provider,
                    service_category=service
                )
            
            provider.onboarding_step = 2
            provider.save()
            
            return Response(
                {
                    'message': 'Step 2 completed successfully',
                    'onboarding_step': provider.onboarding_step,
                    'provider': ServiceProviderSerializer(provider).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def onboarding_step3(self, request):
        """
        Screen 3: Save personal information and documents.
        """
        provider = get_object_or_404(ServiceProvider, user=request.user)
        
        serializer = OnboardingStep3Serializer(data=request.data)
        if serializer.is_valid():
            provider.name = serializer.validated_data['name']
            provider.contact = serializer.validated_data['contact']
            provider.address = serializer.validated_data['address']
            
            if 'profile_photo' in request.FILES:
                provider.profile_photo = request.FILES['profile_photo']
            if 'pan_card' in request.FILES:
                provider.pan_card = request.FILES['pan_card']
            if 'registration_certificate' in request.FILES:
                provider.registration_certificate = request.FILES['registration_certificate']
            
            provider.onboarding_step = 3
            provider.is_onboarding_complete = True
            provider.save()
            
            return Response(
                {
                    'message': 'Step 3 completed successfully. Waiting for admin verification.',
                    'onboarding_step': provider.onboarding_step,
                    'is_onboarding_complete': provider.is_onboarding_complete,
                    'verification_status': provider.verification_status,
                    'provider': ServiceProviderSerializer(provider).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_profile(self, request):
        """
        Get current user's provider profile.
        """
        try:
            provider = ServiceProvider.objects.get(user=request.user)
            serializer = self.get_serializer(provider)
            return Response(serializer.data)
        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Provider profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def status(self, request):
        """
        Check provider verification status and onboarding progress.
        """
        try:
            provider = ServiceProvider.objects.get(user=request.user)
            return Response({
                'onboarding_step': provider.onboarding_step,
                'is_onboarding_complete': provider.is_onboarding_complete,
                'verification_status': provider.verification_status,
                'can_login': provider.can_login,
                'verification_notes': provider.verification_notes if provider.verification_notes else None
            })
        except ServiceProvider.DoesNotExist:
            return Response({
                'onboarding_step': 0,
                'onboarding_complete': False,
                'is_onboarding_complete': False,
                'verification_status': 'not_started',
                'can_login': False,
                'message': 'Provider profile not found. Please complete onboarding.'
            })
    
    def list(self, request):
        """
        List all verified providers. Can filter by service category.
        Excludes the current user's own provider profile if they are a provider.
        """
        queryset = ServiceProvider.objects.filter(
            verification_status='approved',
            is_onboarding_complete=True
        )
        
        # Exclude current user's own provider profile if they are a provider
        if request.user.is_authenticated and request.user.role == 'provider':
            try:
                user_provider = ServiceProvider.objects.get(user=request.user)
                queryset = queryset.exclude(id=user_provider.id)
            except ServiceProvider.DoesNotExist:
                pass
        
        # Filter by service category if provided
        service_id = request.query_params.get('service', None)
        if service_id:
            try:
                service_category = ServiceCategory.objects.get(id=service_id)
                queryset = queryset.filter(services__service_category=service_category).distinct()
            except ServiceCategory.DoesNotExist:
                pass
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
