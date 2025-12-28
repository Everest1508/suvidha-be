from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'title', 'notification_type_display', 
        'is_read_display', 'created_at', 'message_preview'
    ]
    list_filter = ['is_read', 'notification_type', 'created_at']
    search_fields = [
        'user__username', 'user__email',
        'title', 'message'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('Status', {
            'fields': ('is_read', 'related_id')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def notification_type_display(self, obj):
        colors = {
            'booking_created': '#2196F3',
            'booking_accepted': '#4CAF50',
            'booking_completed': '#8BC34A',
            'verification_approved': '#4CAF50',
            'verification_rejected': '#F44336',
            'general': '#666',
        }
        color = colors.get(obj.notification_type, '#666')
        return format_html(
            '<span style="color: {}; font-weight: 500;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_display.short_description = 'Type'
    
    def is_read_display(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: orange;">✗ Unread</span>')
    is_read_display.short_description = 'Status'
    
    def message_preview(self, obj):
        if obj.message:
            preview = obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
            return preview
        return '-'
    message_preview.short_description = 'Message'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'

