from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, F, DecimalField, Value, Case, When
from django.db.models.functions import ACos, Cos, Radians, Sin
from decimal import Decimal
from urllib.parse import unquote_plus
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
        List all verified providers. Supports filtering by:
        - service: service category ID
        - search: search query (name, address, location_string)
        - latitude, longitude: for location-based filtering
        - radius: radius in kilometers (default: 10km)
        - min_price, max_price: price range filtering
        - available_only: filter only available providers (true/false)
        - sort_by: 'price_low' or 'price_high' for price sorting
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
        
        # Fuzzy search: handle URL encoding, strip, split into words, match any word or substring in multiple fields
        search_query = request.query_params.get('search', None)
        if search_query:
            # URL decode the search query (handles +, %20, etc.)
            original_query = search_query
            search_query = unquote_plus(search_query).strip()
            
            # Debug logging
            print(f"🔍 Search query - Original: '{original_query}', Decoded: '{search_query}'")
            
            if search_query:
                # Normalize: split into words (e.g. "cars " -> ["cars"], "car wash" -> ["car", "wash"])
                words = [w.strip() for w in search_query.split() if w.strip()]
                print(f"🔍 Search words: {words}")
                
                if words:
                    # Build search conditions: match if ANY word (or fuzzy variant) appears in ANY of these fields
                    search_conditions = Q()
                    
                    def _search_tokens_for_word(word):
                        """Return list of strings to search: full word + typo + prefixes (min 4 chars) so 'painter' matches 'Paint' but not 'int' in 'Plumber'."""
                        tokens = [word]
                        # Typo: word minus last char (e.g. "painter" -> "painte")
                        if len(word) > 1:
                            short = word[:-1]
                            if short not in tokens:
                                tokens.append(short)
                        # Prefixes of length >= 4 only (e.g. "painter" -> "pain", "paint", "painte") so "Paint" matches
                        # Avoid short substrings like "int", "ain" that match unrelated words (Electronics, Plumber)
                        if len(word) > 4:
                            for length in range(4, len(word)):
                                prefix = word[:length]
                                if prefix not in tokens:
                                    tokens.append(prefix)
                        return tokens
                    
                    for word in words:
                        tokens = _search_tokens_for_word(word)
                        for token in tokens:
                            if len(token) < 3:
                                continue
                            word_condition = (
                                Q(name__icontains=token) |
                                Q(address__icontains=token) |
                                Q(location_string__icontains=token) |
                                Q(contact__icontains=token) |
                                Q(services__service_category__name__icontains=token)
                            )
                            search_conditions |= word_condition
                    
                    # Also try matching the entire search query as a phrase (for exact phrase matches)
                    if len(words) > 1:
                        full_query_condition = (
                            Q(name__icontains=search_query) |
                            Q(address__icontains=search_query) |
                            Q(location_string__icontains=search_query) |
                            Q(contact__icontains=search_query) |
                            Q(services__service_category__name__icontains=search_query)
                        )
                        search_conditions |= full_query_condition
                    
                    queryset = queryset.filter(search_conditions).distinct()
                    print(f"🔍 Found {queryset.count()} providers matching search (fuzzy)")
        
        # Location-based filtering (near me)
        latitude = request.query_params.get('latitude', None)
        longitude = request.query_params.get('longitude', None)
        radius_param = request.query_params.get('radius', None)
        try:
            radius = float(radius_param) if (radius_param is not None and str(radius_param).strip() != '') else 10.0
        except (ValueError, TypeError):
            radius = 10.0
        # Ensure radius is positive
        radius = max(0.1, radius)

        if latitude and longitude:
            try:
                lat = float(latitude)
                lon = float(longitude)
                # Haversine formula for distance calculation
                # Filter providers within radius
                # This is a simplified version - for production, consider using PostGIS
                from math import radians, cos, sin, asin, sqrt
                
                def haversine_distance(lat1, lon1, lat2, lon2):
                    """Calculate distance between two points in kilometers"""
                    R = 6371  # Earth radius in kilometers
                    dlat = radians(lat2 - lat1)
                    dlon = radians(lon2 - lon1)
                    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    return R * c
                
                # Filter providers that have valid coordinates and are within radius
                providers_with_location = []
                qs_with_location = queryset.filter(latitude__isnull=False, longitude__isnull=False)
                for provider in qs_with_location:
                    distance = haversine_distance(
                        lat, lon,
                        float(provider.latitude),
                        float(provider.longitude)
                    )
                    if distance <= radius:
                        providers_with_location.append(provider.id)
                
                print(f"[DEBUG] Radius filter: radius={radius} km, request param='{radius_param}', within_radius={len(providers_with_location)} providers")
                queryset = queryset.filter(id__in=providers_with_location)
            except (ValueError, TypeError) as e:
                print(f"[DEBUG] Radius filter error (skipping location filter): {e}")
                pass
        
        # Price range filtering
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        if min_price:
            try:
                min_price_val = Decimal(min_price)
                queryset = queryset.filter(
                    Q(min_price__isnull=True) | Q(min_price__gte=min_price_val)
                )
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                max_price_val = Decimal(max_price)
                queryset = queryset.filter(
                    Q(max_price__isnull=True) | Q(max_price__lte=max_price_val)
                )
            except (ValueError, TypeError):
                pass
        
        # Availability filter - check current availability based on schedule
        available_only = request.query_params.get('available_only', 'false').lower() == 'true'
        if available_only:
            # Filter providers who are currently available based on their schedule
            from django.utils import timezone
            from datetime import datetime, time
            
            now = timezone.now()
            current_day = now.strftime('%A').lower()
            current_time = now.time()
            
            day_map = {
                'monday': 0,
                'tuesday': 1,
                'wednesday': 2,
                'thursday': 3,
                'friday': 4,
                'saturday': 5,
                'sunday': 6,
            }
            
            current_day_num = day_map.get(current_day, -1)
            
            # Filter providers whose schedule matches current day and time
            available_providers = []
            for provider in queryset:
                if provider.is_available:
                    available_providers.append(provider.id)
            
            queryset = queryset.filter(id__in=available_providers)
        
        # Sort by price
        sort_by = request.query_params.get('sort_by', None)
        if sort_by == 'price_low':
            queryset = queryset.order_by('min_price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-max_price', '-min_price')
        else:
            queryset = queryset.order_by('-created_at')
        
        # Debug: list providers being returned with distance
        from math import radians, cos, sin, asin, sqrt
        def _haversine_km(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return round(R * c, 2)

        provider_list = list(queryset)
        user_lat = float(latitude) if latitude else None
        user_lon = float(longitude) if longitude else None
        total_distance_km = 0.0

        print(f"[DEBUG] Providers list: total={len(provider_list)}")
        print(f"[DEBUG] Query params: latitude={latitude}, longitude={longitude}, radius={radius}, service={service_id}, search={request.query_params.get('search')}")
        for i, p in enumerate(provider_list):
            dist_km = None
            if user_lat is not None and user_lon is not None and p.latitude is not None and p.longitude is not None:
                dist_km = _haversine_km(user_lat, user_lon, float(p.latitude), float(p.longitude))
                total_distance_km += dist_km
            dist_str = f" distance={dist_km} km" if dist_km is not None else " distance=N/A"
            print(f"  [{i+1}] id={p.id} name={p.name} lat={p.latitude} lon={p.longitude}{dist_str}")
        if user_lat is not None and user_lon is not None:
            print(f"[DEBUG] Total distance (sum of all): {round(total_distance_km, 2)} km")

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def update_availability(self, request):
        """
        Update provider availability schedule.
        """
        try:
            provider = ServiceProvider.objects.get(user=request.user)
            available_from_day = request.data.get('available_from_day', None)
            available_to_day = request.data.get('available_to_day', None)
            available_start_time = request.data.get('available_start_time', None)
            available_end_time = request.data.get('available_end_time', None)
            
            if available_from_day:
                provider.available_from_day = available_from_day
            if available_to_day:
                provider.available_to_day = available_to_day
            if available_start_time:
                from datetime import datetime
                try:
                    provider.available_start_time = datetime.strptime(available_start_time, '%H:%M').time()
                except ValueError:
                    return Response(
                        {'error': 'Invalid start_time format. Use HH:MM (e.g., 09:00)'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            if available_end_time:
                from datetime import datetime
                try:
                    provider.available_end_time = datetime.strptime(available_end_time, '%H:%M').time()
                except ValueError:
                    return Response(
                        {'error': 'Invalid end_time format. Use HH:MM (e.g., 17:00)'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            provider.save()
            return Response({
                'message': 'Availability schedule updated successfully',
                'available_from_day': provider.available_from_day,
                'available_to_day': provider.available_to_day,
                'available_start_time': str(provider.available_start_time) if provider.available_start_time else None,
                'available_end_time': str(provider.available_end_time) if provider.available_end_time else None,
                'is_available': provider.is_available
            })
        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Provider profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def update_price_range(self, request):
        """
        Update provider price range.
        """
        try:
            provider = ServiceProvider.objects.get(user=request.user)
            min_price = request.data.get('min_price', None)
            max_price = request.data.get('max_price', None)
            
            if min_price is not None:
                try:
                    provider.min_price = Decimal(str(min_price))
                except (ValueError, TypeError):
                    return Response(
                        {'error': 'Invalid min_price value'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if max_price is not None:
                try:
                    provider.max_price = Decimal(str(max_price))
                except (ValueError, TypeError):
                    return Response(
                        {'error': 'Invalid max_price value'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate min_price <= max_price
            if provider.min_price and provider.max_price:
                if provider.min_price > provider.max_price:
                    return Response(
                        {'error': 'min_price must be less than or equal to max_price'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            provider.save()
            return Response({
                'message': 'Price range updated successfully',
                'min_price': str(provider.min_price) if provider.min_price else None,
                'max_price': str(provider.max_price) if provider.max_price else None
            })
        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Provider profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
