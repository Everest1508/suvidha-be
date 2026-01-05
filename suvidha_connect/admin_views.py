from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.html import format_html
from django.db.models import Count
from accounts.models import User
from providers.models import ServiceProvider
from bookings.models import Booking
from services.models import ServiceCategory
from reviews.models import Review


@staff_member_required
def admin_about_view(request):
    """Custom About page for admin panel"""
    
    # Get statistics
    total_users = User.objects.count()
    total_customers = User.objects.filter(role='customer').count()
    total_providers = User.objects.filter(role='provider').count()
    total_verified_providers = ServiceProvider.objects.filter(verification_status='approved').count()
    total_pending_providers = ServiceProvider.objects.filter(verification_status='pending').count()
    total_bookings = Booking.objects.count()
    total_service_categories = ServiceCategory.objects.filter(is_active=True).count()
    total_reviews = Review.objects.count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_bookings = Booking.objects.order_by('-created_at')[:5]
    
    # Booking statistics by status
    booking_stats = Booking.objects.values('status').annotate(count=Count('id')).order_by('-count')
    
    context = {
        'title': 'About Sahayak Admin Panel',
        'stats': {
            'total_users': total_users,
            'total_customers': total_customers,
            'total_providers': total_providers,
            'verified_providers': total_verified_providers,
            'pending_providers': total_pending_providers,
            'total_bookings': total_bookings,
            'total_service_categories': total_service_categories,
            'total_reviews': total_reviews,
        },
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'booking_stats': booking_stats,
    }
    
    return render(request, 'admin/about.html', context)

