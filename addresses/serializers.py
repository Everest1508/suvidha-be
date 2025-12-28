from rest_framework import serializers
from .models import SavedAddress


class SavedAddressSerializer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = SavedAddress
        fields = [
            'id', 'user', 'label', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'is_default',
            'created_at', 'updated_at', 'full_address'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_full_address(self, obj):
        return obj.get_full_address()

