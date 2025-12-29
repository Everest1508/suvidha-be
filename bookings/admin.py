from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer', 'provider', 'service_category', 
        'status_display', 'price', 'scheduled_date', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'service_category', 'provider']
    search_fields = [
        'customer__username', 'customer__email', 
        'provider__name', 'provider__user__username',
        'description', 'address'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'accepted_at', 'completed_at',
        'status_history'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('customer', 'provider', 'service_category', 'status')
        }),
        ('Service Details', {
            'fields': ('description', 'address', 'scheduled_date', 'price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'accepted_at', 'completed_at', 'status_history'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['accept_bookings', 'mark_completed', 'mark_cancelled', 'mark_in_progress']
    
    def status_display(self, obj):
        colors = {
            'pending': '#FFA500',
            'negotiation': '#FF9800',
            'accepted': '#2196F3',
            'in_progress': '#9C27B0',
            'completed': '#4CAF50',
            'payment': '#9C27B0',
            'cancelled': '#F44336',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def status_history(self, obj):
        history = []
        if obj.created_at:
            history.append(f"Created: {obj.created_at.strftime('%Y-%m-%d %H:%M')}")
        if obj.accepted_at:
            history.append(f"Accepted: {obj.accepted_at.strftime('%Y-%m-%d %H:%M')}")
        if obj.completed_at:
            history.append(f"Completed: {obj.completed_at.strftime('%Y-%m-%d %H:%M')}")
        return format_html('<br>'.join(history) if history else 'No history')
    status_history.short_description = 'Status History'
    
    def accept_bookings(self, request, queryset):
        from django.utils import timezone
        count = 0
        for booking in queryset.filter(status='pending'):
            booking.status = 'accepted'
            booking.accepted_at = timezone.now()
            booking.save()
            count += 1
        self.message_user(request, f'{count} booking(s) accepted.')
    accept_bookings.short_description = 'Accept selected pending bookings'
    
    def mark_completed(self, request, queryset):
        from django.utils import timezone
        count = 0
        for booking in queryset.exclude(status='cancelled'):
            booking.status = 'completed'
            if not booking.completed_at:
                booking.completed_at = timezone.now()
            booking.save()
            count += 1
        self.message_user(request, f'{count} booking(s) marked as completed.')
    mark_completed.short_description = 'Mark as Completed'
    
    def mark_cancelled(self, request, queryset):
        count = queryset.exclude(status='completed').update(status='cancelled')
        self.message_user(request, f'{count} booking(s) cancelled.')
    mark_cancelled.short_description = 'Cancel selected bookings'
    
    def mark_in_progress(self, request, queryset):
        count = queryset.filter(status='accepted').update(status='in_progress')
        self.message_user(request, f'{count} booking(s) marked as in progress.')
    mark_in_progress.short_description = 'Mark as In Progress'

