from rest_framework import serializers
from .models import Review
from accounts.serializers import UserSerializer
from providers.serializers import ServiceProviderSerializer
from providers.models import ServiceProvider
from services.serializers import ServiceCategorySerializer
from services.models import ServiceCategory


class ReviewSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    provider = ServiceProviderSerializer(read_only=True)
    service_category = ServiceCategorySerializer(read_only=True)
    customer_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProvider.objects.all(),
        source='provider',
        write_only=True,
        required=True
    )
    service_category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(),
        source='service_category',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Review
        fields = [
            'id', 'provider', 'customer', 'rating', 'comment',
            'service_category', 'created_at', 'updated_at',
            'customer_name', 'provider_name', 'service_name',
            'provider_id', 'service_category_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'customer']
    
    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.username
    
    def get_provider_name(self, obj):
        return obj.provider.name or obj.provider.user.username
    
    def get_service_name(self, obj):
        return obj.service_category.name if obj.service_category else None

