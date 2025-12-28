from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'provider', 'service_category', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'service_category']
    search_fields = ['customer__username', 'provider__name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'accepted_at', 'completed_at']

