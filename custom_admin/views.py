from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from accounts.models import User
from providers.models import ServiceProvider
from services.models import ServiceCategory
from bookings.models import Booking
from reviews.models import Review
from .forms import ServiceCategoryForm, UserForm, ProviderApprovalForm, EmailSettingsForm
from .icon_list import ICONSAX_ICONS, get_icon_name
from .models import EmailSettings


def is_admin(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and user.is_staff


def admin_login(request):
    """Custom login page for Sahayyak Admin"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('custom_admin:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        next_url = request.POST.get('next', '')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'custom_admin/login.html', {'next': next_url})
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                if next_url:
                    try:
                        return redirect(next_url)
                    except:
                        pass
                return redirect('custom_admin:dashboard')
            else:
                messages.error(request, 'You do not have permission to access the admin panel.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    next_url = request.GET.get('next', '')
    return render(request, 'custom_admin/login.html', {'next': next_url})


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def admin_logout(request):
    """Logout from admin panel"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('custom_admin:login')


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def dashboard(request):
    """Sahayyak admin dashboard"""
    stats = {
        'total_users': User.objects.count(),
        'total_customers': User.objects.filter(role='customer').count(),
        'total_providers': User.objects.filter(role='provider').count(),
        'pending_providers': ServiceProvider.objects.filter(verification_status='pending').count(),
        'approved_providers': ServiceProvider.objects.filter(verification_status='approved').count(),
        'total_bookings': Booking.objects.count(),
        'total_categories': ServiceCategory.objects.count(),
        'active_categories': ServiceCategory.objects.filter(is_active=True).count(),
        'total_reviews': Review.objects.count(),
    }
    
    recent_providers = ServiceProvider.objects.filter(verification_status='pending').order_by('-id')[:5]
    recent_bookings = Booking.objects.order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_providers': recent_providers,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'custom_admin/dashboard.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def users_list(request):
    """List all users"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    users = users.order_by('-date_joined')
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'custom_admin/users_list.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def user_edit(request, user_id):
    """Edit user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('custom_admin:users_list')
    else:
        form = UserForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'custom_admin/user_edit.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def user_delete(request, user_id):
    """Delete user (with confirmation). Cannot delete self or superusers."""
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete.pk == request.user.pk:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('custom_admin:users_list')
    if user_to_delete.is_superuser:
        messages.error(request, 'Cannot delete a superuser account.')
        return redirect('custom_admin:users_list')

    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'User "{username}" has been deleted.')
        return redirect('custom_admin:users_list')

    context = {'user_to_delete': user_to_delete}
    return render(request, 'custom_admin/user_delete.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def providers_list(request):
    """List all providers with filtering"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    providers = ServiceProvider.objects.select_related('user').all()
    
    if status_filter:
        providers = providers.filter(verification_status=status_filter)
    
    if search_query:
        providers = providers.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    providers = providers.order_by('-id')
    
    paginator = Paginator(providers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'custom_admin/providers_list.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def provider_detail(request, provider_id):
    """View provider details and approve/reject"""
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    
    if request.method == 'POST':
        form = ProviderApprovalForm(request.POST)
        if form.is_valid():
            provider.verification_status = form.cleaned_data['verification_status']
            provider.verification_notes = form.cleaned_data.get('verification_notes', '')
            provider.verified_by = request.user
            from django.utils import timezone
            provider.verified_at = timezone.now()
            provider.save()
            
            status = 'approved' if provider.verification_status == 'approved' else 'rejected'
            messages.success(request, f'Provider {status} successfully.')
            return redirect('custom_admin:providers_list')
    else:
        form = ProviderApprovalForm(initial={
            'verification_status': provider.verification_status,
            'verification_notes': provider.verification_notes,
        })
    
    context = {
        'provider': provider,
        'form': form,
    }
    return render(request, 'custom_admin/provider_detail.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def categories_list(request):
    """List all service categories"""
    search_query = request.GET.get('search', '')
    active_filter = request.GET.get('active', '')
    
    categories = ServiceCategory.objects.all()
    
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(slug__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if active_filter == 'true':
        categories = categories.filter(is_active=True)
    elif active_filter == 'false':
        categories = categories.filter(is_active=False)
    
    categories = categories.order_by('name')
    
    # Add icon display names
    for category in categories:
        category.icon_display = get_icon_name(category.icon)
    
    context = {
        'categories': categories,
        'search_query': search_query,
        'active_filter': active_filter,
    }
    return render(request, 'custom_admin/categories_list.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def category_add(request):
    """Add new service category"""
    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service category added successfully.')
            return redirect('custom_admin:categories_list')
    else:
        form = ServiceCategoryForm()
    
    context = {
        'form': form,
        'icons': ICONSAX_ICONS,
    }
    return render(request, 'custom_admin/category_form.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def category_edit(request, category_id):
    """Edit service category"""
    category = get_object_or_404(ServiceCategory, id=category_id)
    
    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service category updated successfully.')
            return redirect('custom_admin:categories_list')
    else:
        form = ServiceCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'icons': ICONSAX_ICONS,
    }
    return render(request, 'custom_admin/category_form.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def category_delete(request, category_id):
    """Delete service category"""
    category = get_object_or_404(ServiceCategory, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Service category "{category_name}" deleted successfully.')
        return redirect('custom_admin:categories_list')
    
    context = {
        'category': category,
    }
    return render(request, 'custom_admin/category_delete.html', context)


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def tickets_list(request):
    """Tickets list page (placeholder until Ticket model is added)."""
    return render(request, 'custom_admin/tickets_list.html', {})


@login_required(login_url='custom_admin:login')
@user_passes_test(is_admin, login_url='custom_admin:login')
def email_settings(request):
    """Configure SMTP email settings (used for password reset etc.)."""
    instance = EmailSettings.objects.first()
    if instance is None:
        instance = EmailSettings.objects.create()
    if request.method == 'POST':
        form = EmailSettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email settings saved. Password reset and other emails will use these settings when enabled.')
            return redirect('custom_admin:email_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmailSettingsForm(instance=instance)
    context = {'form': form, 'email_settings': instance}
    return render(request, 'custom_admin/email_settings.html', context)

