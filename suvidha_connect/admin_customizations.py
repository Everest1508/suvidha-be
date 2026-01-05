"""
Customizations for Django admin panel
Adds links to legal pages and other useful information
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.conf import settings


def get_app_base_url():
    """Get the base URL for the Flutter app"""
    # You can configure this in settings or use request.build_absolute_uri
    return getattr(settings, 'APP_BASE_URL', 'https://suvidhaconnect.pythonanywhere.com')


# Customize admin site
admin.site.site_header = "Sahayak Admin Panel"
admin.site.site_title = "Sahayak Admin"
admin.site.index_title = "Welcome to Sahayak Administration"


# Add custom admin template context
def admin_site_context(request):
    """Add custom context to admin site"""
    app_base_url = get_app_base_url()
    
    legal_links = {
        'terms_conditions': f'{app_base_url}/terms-conditions',
        'privacy_policy': f'{app_base_url}/privacy-policy',
        'about_us': f'{app_base_url}/about-us',
    }
    
    return {
        'legal_links': legal_links,
        'app_base_url': app_base_url,
    }


# Override admin index template to add legal links
# We'll create a custom admin index template
def get_admin_index_context(request):
    """Get context for admin index page"""
    context = admin_site_context(request)
    return context

