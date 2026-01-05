"""
URL configuration for suvidha_connect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import admin_views

# Customize admin site
admin.site.site_header = "Sahayak Admin Panel"
admin.site.site_title = "Sahayak Admin"
admin.site.index_title = "Welcome to Sahayak Administration"

urlpatterns = [
    path('admin/about/', admin_views.admin_about_view, name='admin_about'),
    path('admin/', admin.site.urls),
    path('custom-admin/', include('custom_admin.urls')),
    path('', include('landing.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api/wallets/', include('accounts.wallet_urls')),  # Wallet endpoints
    path('api/bank-accounts/', include('accounts.bank_account_urls')),  # Bank account endpoints
    path('api/withdrawals/', include('accounts.withdrawal_urls')),  # Withdrawal endpoints
    path('api/services/', include('services.urls')),
    path('api/', include('providers.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/addresses/', include('addresses.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
