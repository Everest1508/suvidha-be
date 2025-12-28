from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceProvider, ProviderService, ReferralCode


class ProviderServiceInline(admin.TabularInline):
    model = ProviderService
    extra = 0
    readonly_fields = ['created_at']


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'verification_status', 'onboarding_step',
        'is_onboarding_complete', 'can_login_display', 'created_at'
    ]
    list_filter = [
        'verification_status', 'is_onboarding_complete',
        'onboarding_step', 'created_at'
    ]
    search_fields = ['name', 'user__username', 'user__email', 'contact', 'location_string']
    readonly_fields = [
        'user', 'created_at', 'updated_at', 'verified_at', 'verified_by',
        'profile_photo_preview', 'pan_card_link', 'registration_certificate_link'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'name', 'contact', 'address', 'profile_photo', 'profile_photo_preview')
        }),
        ('Location Information', {
            'fields': ('latitude', 'longitude', 'location_string', 'referral_code')
        }),
        ('Documents', {
            'fields': ('pan_card', 'pan_card_link', 'registration_certificate', 'registration_certificate_link')
        }),
        ('Verification', {
            'fields': (
                'verification_status', 'verification_notes',
                'verified_at', 'verified_by'
            )
        }),
        ('Onboarding Status', {
            'fields': ('onboarding_step', 'is_onboarding_complete')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [ProviderServiceInline]
    actions = ['approve_providers', 'reject_providers']
    
    def can_login_display(self, obj):
        if obj is None:
            return "-"
        try:
            if obj.can_login:
                return format_html('<span style="color: green;">✓ Can Login</span>')
            return format_html('<span style="color: red;">✗ Cannot Login</span>')
        except Exception:
            return "-"
    can_login_display.short_description = 'Login Status'
    
    def profile_photo_preview(self, obj):
        if obj is None or not obj.profile_photo:
            return "No photo"
        try:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.profile_photo.url
            )
        except Exception:
            return "No photo"
    profile_photo_preview.short_description = 'Profile Photo Preview'
    
    def pan_card_link(self, obj):
        if obj is None or not obj.pan_card:
            return "No document"
        try:
            return format_html(
                '<a href="{}" target="_blank">View PAN Card</a>',
                obj.pan_card.url
            )
        except Exception:
            return "No document"
    pan_card_link.short_description = 'PAN Card'
    
    def registration_certificate_link(self, obj):
        if obj is None or not obj.registration_certificate:
            return "No document"
        try:
            return format_html(
                '<a href="{}" target="_blank">View Registration Certificate</a>',
                obj.registration_certificate.url
            )
        except Exception:
            return "No document"
    registration_certificate_link.short_description = 'Registration Certificate'
    
    def approve_providers(self, request, queryset):
        updated = queryset.update(
            verification_status='approved',
            verified_by=request.user
        )
        self.message_user(request, f'{updated} provider(s) approved.')
    approve_providers.short_description = 'Approve selected providers'
    
    def reject_providers(self, request, queryset):
        updated = queryset.update(verification_status='rejected')
        self.message_user(request, f'{updated} provider(s) rejected.')
    reject_providers.short_description = 'Reject selected providers'
    
    def save_model(self, request, obj, form, change):
        if change and 'verification_status' in form.changed_data:
            if obj.verification_status == 'approved' and not obj.verified_by:
                obj.verified_by = request.user
            if obj.verification_status == 'approved' and not obj.verified_at:
                from django.utils import timezone
                obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'verified_by').prefetch_related('services')


@admin.register(ProviderService)
class ProviderServiceAdmin(admin.ModelAdmin):
    list_display = ['provider', 'service_category', 'created_at']
    list_filter = ['service_category', 'created_at']
    search_fields = ['provider__name', 'service_category__name']


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'used_by', 'created_at', 'used_at']
    list_filter = ['created_at', 'used_at']
    search_fields = ['code', 'used_by__name']
    readonly_fields = ['created_at', 'used_at']
