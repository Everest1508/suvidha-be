from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for managing Service Categories.
    Supports full CRUD operations: Create, Read, Update, Delete
    """
    list_display = [
        'name', 'slug', 'icon', 'is_active', 
        'provider_count', 'created_at', 'actions_column'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description', 'icon']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'provider_count_display']
    list_editable = ['is_active']  # Allow quick editing of active status
    list_per_page = 25
    ordering = ['name']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('name', 'slug', 'icon', 'description', 'is_active'),
            'description': 'Enter the service category details. The slug will be auto-generated from the name.'
        }),
        ('Statistics', {
            'fields': ('provider_count_display',),
            'classes': ('collapse',),
            'description': 'Number of providers offering this service category.'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_services', 'deactivate_services', 'duplicate_services']
    
    def is_active_display(self, obj):
        """Display active status with color coding"""
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactive</span>')
    is_active_display.short_description = 'Status'
    
    def provider_count(self, obj):
        """Display number of providers offering this service"""
        count = obj.providers.count()
        if count > 0:
            # Link to ProviderService admin filtered by this category
            url = reverse('admin:providers_providerservice_changelist')
            return format_html(
                '<a href="{}?service_category__id__exact={}" style="font-weight: bold; color: #417690;">{}</a>',
                url, obj.id, count
            )
        return format_html('<strong style="color: #999;">0</strong>')
    provider_count.short_description = 'Providers'
    
    def provider_count_display(self, obj):
        """Detailed provider count for detail view"""
        count = obj.providers.count()
        if count > 0:
            # Link to ProviderService admin filtered by this category
            url = reverse('admin:providers_providerservice_changelist')
            return format_html(
                '<strong>{}</strong> provider(s) offering this service. '
                '<a href="{}?service_category__id__exact={}">View providers →</a>',
                count, url, obj.id
            )
        return f"{count} provider(s) offering this service"
    provider_count_display.short_description = 'Provider Count'
    
    def actions_column(self, obj):
        """Quick action buttons in list view"""
        if obj.pk:
            edit_url = reverse('admin:services_servicecategory_change', args=[obj.pk])
            delete_url = reverse('admin:services_servicecategory_delete', args=[obj.pk])
            return format_html(
                '<a href="{}" class="button" style="margin-right: 5px;">Edit</a> '
                '<a href="{}" class="deletelink" style="color: #ba2121;">Delete</a>',
                edit_url, delete_url
            )
        return '-'
    actions_column.short_description = 'Actions'
    actions_column.allow_tags = True
    
    def activate_services(self, request, queryset):
        """Bulk action to activate selected services"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'Successfully activated {updated} service categor{("y" if updated == 1 else "ies")}.',
            level='SUCCESS'
        )
    activate_services.short_description = 'Activate selected service categories'
    
    def deactivate_services(self, request, queryset):
        """Bulk action to deactivate selected services"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'Successfully deactivated {updated} service categor{("y" if updated == 1 else "ies")}.',
            level='SUCCESS'
        )
    deactivate_services.short_description = 'Deactivate selected service categories'
    
    def duplicate_services(self, request, queryset):
        """Bulk action to duplicate selected services"""
        duplicated = 0
        for service in queryset:
            # Create a copy with modified name and slug
            service.pk = None
            service.name = f"{service.name} (Copy)"
            service.slug = f"{service.slug}-copy"
            service.is_active = False  # Deactivate duplicates by default
            service.save()
            duplicated += 1
        
        self.message_user(
            request,
            f'Successfully duplicated {duplicated} service categor{("y" if duplicated == 1 else "ies")}.',
            level='SUCCESS'
        )
    duplicate_services.short_description = 'Duplicate selected service categories'
    
    def get_readonly_fields(self, request, obj=None):
        """Make created_at and updated_at readonly"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Editing an existing object
            readonly.append('created_at')
        return readonly
    
    def save_model(self, request, obj, form, change):
        """Override save to add helpful messages"""
        if change:
            message = f'Service category "{obj.name}" was updated successfully.'
        else:
            message = f'Service category "{obj.name}" was created successfully.'
        
        super().save_model(request, obj, form, change)
        self.message_user(request, message, level='SUCCESS')
