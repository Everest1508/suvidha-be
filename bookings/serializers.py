from rest_framework import serializers
from .models import Booking
from accounts.serializers import UserSerializer
from providers.serializers import ServiceProviderSerializer
from providers.models import ServiceProvider
from services.serializers import ServiceCategorySerializer
from services.models import ServiceCategory
from addresses.models import SavedAddress
from addresses.serializers import SavedAddressSerializer


class BookingSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    provider = ServiceProviderSerializer(read_only=True)
    service_category = ServiceCategorySerializer(read_only=True)
    proposed_by = UserSerializer(read_only=True)
    saved_address = SavedAddressSerializer(read_only=True)
    customer_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProvider.objects.filter(verification_status='approved'),
        source='provider',
        write_only=True,
        required=True
    )
    service_category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.filter(is_active=True),
        source='service_category',
        write_only=True,
        required=True
    )
    saved_address_id = serializers.PrimaryKeyRelatedField(
        queryset=SavedAddress.objects.none(),
        source='saved_address',
        write_only=True,
        required=True,
        error_messages={'required': 'Please select a saved address.'}
    )
    
    class Meta:
        model = Booking
        fields = [
            'id', 'customer', 'provider', 'service_category',
            'status', 'description', 'address', 'saved_address', 'scheduled_date',
            'price', 'proposed_price', 'proposed_by', 'price_locked', 'created_at', 'updated_at', 'accepted_at', 'completed_at',
            'customer_name', 'provider_name', 'service_name',
            'provider_id', 'service_category_id', 'saved_address_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'accepted_at', 'completed_at', 'customer', 'status', 'price_locked', 'proposed_by', 'address']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user:
            self.fields['saved_address_id'].queryset = SavedAddress.objects.filter(user=request.user)
    
    def create(self, validated_data):
        saved_address = validated_data.get('saved_address')
        if saved_address:
            validated_data['address'] = saved_address.get_full_address()
        return super().create(validated_data)
    
    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.username
    
    def get_provider_name(self, obj):
        return obj.provider.name or obj.provider.user.username
    
    def get_service_name(self, obj):
        return obj.service_category.name

