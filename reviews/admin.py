from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer', 'provider', 'rating_display', 
        'service_category', 'created_at', 'comment_preview'
    ]
    list_filter = ['rating', 'created_at', 'service_category', 'provider']
    search_fields = [
        'customer__username', 'customer__email',
        'provider__name', 'provider__user__username',
        'comment'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('customer', 'provider', 'service_category', 'rating')
        }),
        ('Review Content', {
            'fields': ('comment',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        colors = {
            5: '#4CAF50',
            4: '#8BC34A',
            3: '#FFC107',
            2: '#FF9800',
            1: '#F44336',
        }
        color = colors.get(obj.rating, '#666')
        return format_html(
            '<span style="color: {}; font-size: 16px;">{}</span>',
            color,
            stars
        )
    rating_display.short_description = 'Rating'
    
    def comment_preview(self, obj):
        if obj.comment:
            preview = obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
            return preview
        return '-'
    comment_preview.short_description = 'Comment'

