from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'icon', 'is_active_display', 
        'provider_count', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'provider_count_display']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('name', 'slug', 'icon', 'description', 'is_active')
        }),
        ('Statistics', {
            'fields': ('provider_count_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_services', 'deactivate_services']
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_display.short_description = 'Status'
    
    def provider_count(self, obj):
        count = obj.providers.count()
        return format_html('<strong>{}</strong>', count)
    provider_count.short_description = 'Providers'
    
    def provider_count_display(self, obj):
        count = obj.providers.count()
        return f"{count} provider(s) offering this service"
    provider_count_display.short_description = 'Provider Count'
    
    def activate_services(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} service(s) activated.')
    activate_services.short_description = 'Activate selected services'
    
    def deactivate_services(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} service(s) deactivated.')
    deactivate_services.short_description = 'Deactivate selected services'
