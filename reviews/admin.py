from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'provider', 'rating', 'service_category', 'created_at']
    list_filter = ['rating', 'created_at', 'service_category']
    search_fields = ['customer__username', 'provider__name', 'comment']
    readonly_fields = ['created_at', 'updated_at']

