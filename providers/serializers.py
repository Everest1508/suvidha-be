from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import models
from .models import ServiceProvider, ProviderService, ReferralCode
from services.serializers import ServiceCategorySerializer
from services.models import ServiceCategory

User = get_user_model()


class ProviderServiceSerializer(serializers.ModelSerializer):
    service_category = ServiceCategorySerializer(read_only=True)
    service_category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.filter(is_active=True),
        source='service_category',
        write_only=True
    )
    
    class Meta:
        model = ProviderService
        fields = ['id', 'service_category', 'service_category_id', 'created_at']


class ServiceProviderSerializer(serializers.ModelSerializer):
    services = ProviderServiceSerializer(many=True, read_only=True)
    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'name', 'contact', 'address', 'profile_photo',
            'latitude', 'longitude', 'location_string', 'referral_code',
            'pan_card', 'registration_certificate',
            'verification_status', 'onboarding_step', 'is_onboarding_complete',
            'services', 'service_ids',
            'average_rating', 'total_reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['verification_status', 'verified_at', 'verified_by']
    
    def get_average_rating(self, obj):
        """Calculate average rating from reviews"""
        from reviews.models import Review
        reviews = Review.objects.filter(provider=obj)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0, 1)
        return 0.0
    
    def get_total_reviews(self, obj):
        """Get total number of reviews"""
        from reviews.models import Review
        return Review.objects.filter(provider=obj).count()


class OnboardingStep1Serializer(serializers.Serializer):
    """Screen 1: Location and Referral Code"""
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    location_string = serializers.CharField(max_length=500, required=True)
    referral_code = serializers.CharField(max_length=50, required=False, allow_blank=True)


class OnboardingStep2Serializer(serializers.Serializer):
    """Screen 2: Service Selection"""
    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1,
        help_text="List of service category IDs"
    )


class OnboardingStep3Serializer(serializers.Serializer):
    """Screen 3: Personal Information and Documents"""
    name = serializers.CharField(max_length=200, required=True)
    contact = serializers.CharField(max_length=15, required=True)
    address = serializers.CharField(required=True)
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    pan_card = serializers.FileField(required=True)
    registration_certificate = serializers.FileField(required=True)


class ProviderRegistrationSerializer(serializers.Serializer):
    """Complete registration for new provider"""
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    phone = serializers.CharField(required=True)
    
    # Step 1 data
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    location_string = serializers.CharField(max_length=500, required=True)
    referral_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    # Step 2 data
    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1
    )
    
    # Step 3 data
    name = serializers.CharField(max_length=200, required=True)
    contact = serializers.CharField(max_length=15, required=True)
    address = serializers.CharField(required=True)
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    pan_card = serializers.FileField(required=True)
    registration_certificate = serializers.FileField(required=True)
    
    def create(self, validated_data):
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data['phone'],
            role='provider'
        )
        
        # Create service provider
        provider = ServiceProvider.objects.create(
            user=user,
            name=validated_data['name'],
            contact=validated_data['contact'],
            address=validated_data['address'],
            latitude=validated_data['latitude'],
            longitude=validated_data['longitude'],
            location_string=validated_data['location_string'],
            referral_code=validated_data.get('referral_code', ''),
            profile_photo=validated_data.get('profile_photo'),
            pan_card=validated_data['pan_card'],
            registration_certificate=validated_data['registration_certificate'],
            onboarding_step=3,
            is_onboarding_complete=True
        )
        
        # Add services
        for service_id in validated_data['service_ids']:
            ProviderService.objects.create(
                provider=provider,
                service_category_id=service_id
            )
        
        # Handle referral code if provided
        if validated_data.get('referral_code'):
            ReferralCode.objects.get_or_create(
                code=validated_data['referral_code'],
                defaults={'used_by': provider}
            )
        
        return provider

