from django.contrib import admin
from django.utils.html import format_html
from .models import SavedAddress


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'label', 'city', 'state', 
        'is_default_display', 'created_at', 'full_address_preview'
    ]
    list_filter = ['is_default', 'city', 'state', 'created_at']
    search_fields = [
        'user__username', 'user__email',
        'label', 'address_line1', 'city', 'state', 'postal_code'
    ]
    readonly_fields = ['created_at', 'updated_at', 'full_address_display']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'label', 'is_default')
        }),
        ('Address Details', {
            'fields': (
                'address_line1', 'address_line2',
                'city', 'state', 'postal_code', 'country',
                'full_address_display'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['set_as_default', 'remove_default']
    
    def is_default_display(self, obj):
        if obj.is_default:
            return format_html('<span style="color: green; font-weight: bold;">✓ Default</span>')
        return '-'
    is_default_display.short_description = 'Default'
    
    def full_address_preview(self, obj):
        return obj.get_full_address()
    full_address_preview.short_description = 'Full Address'
    
    def full_address_display(self, obj):
        return format_html('<p style="font-size: 14px; padding: 10px; background: #f5f5f5; border-radius: 4px;">{}</p>', 
                          obj.get_full_address())
    full_address_display.short_description = 'Full Address'
    
    def set_as_default(self, request, queryset):
        count = 0
        for address in queryset:
            # Unset other default addresses for this user
            SavedAddress.objects.filter(user=address.user, is_default=True).update(is_default=False)
            address.is_default = True
            address.save()
            count += 1
        self.message_user(request, f'{count} address(es) set as default.')
    set_as_default.short_description = 'Set as default address'
    
    def remove_default(self, request, queryset):
        updated = queryset.update(is_default=False)
        self.message_user(request, f'{updated} address(es) removed from default.')
    remove_default.short_description = 'Remove default status'
