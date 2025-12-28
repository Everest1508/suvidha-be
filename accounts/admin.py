from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'email', 'phone', 'role', 'is_staff', 
        'is_active', 'profile_photo_preview', 'date_joined'
    ]
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login', 'profile_photo_preview']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Additional Info', {
            'fields': ('role', 'phone', 'profile_photo', 'profile_photo_preview')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'first_name', 'last_name', 'email')
        }),
    )
    
    actions = ['make_provider', 'make_customer', 'deactivate_users', 'activate_users']
    
    def profile_photo_preview(self, obj):
        if obj and obj.profile_photo:
            try:
                return format_html(
                    '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 50%;" />',
                    obj.profile_photo.url
                )
            except:
                return "No photo"
        return "No photo"
    profile_photo_preview.short_description = 'Profile Photo'
    
    def make_provider(self, request, queryset):
        updated = queryset.update(role='provider')
        self.message_user(request, f'{updated} user(s) changed to provider.')
    make_provider.short_description = 'Change role to Provider'
    
    def make_customer(self, request, queryset):
        updated = queryset.update(role='customer')
        self.message_user(request, f'{updated} user(s) changed to customer.')
    make_customer.short_description = 'Change role to Customer'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated.')
    activate_users.short_description = 'Activate selected users'
