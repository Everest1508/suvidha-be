from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from .models import Booking
from .serializers import BookingSerializer
from notifications.models import Notification


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Custom authentication class that doesn't enforce CSRF for mobile apps."""
    def enforce_csrf(self, request):
        pass


@method_decorator(csrf_exempt, name='dispatch')
class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for booking operations."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    def get_queryset(self):
        """Return bookings based on user role."""
        user = self.request.user
        
        if user.role == 'provider':
            # Providers see bookings for their services
            try:
                from providers.models import ServiceProvider
                provider = ServiceProvider.objects.get(user=user)
                return Booking.objects.filter(provider=provider)
            except ServiceProvider.DoesNotExist:
                return Booking.objects.none()
        else:
            # Customers see their own bookings
            return Booking.objects.filter(customer=user)
    
    def create(self, request):
        """Create a new booking."""
        # Handle both JSON and form data
        if hasattr(request.data, 'copy'):
            data = request.data.copy()
        else:
            data = dict(request.data)
        
        # Don't set customer in data, let serializer handle it
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            booking = serializer.save(customer=request.user)
            
            # Create notification for provider about new booking
            try:
                provider_user = booking.provider.user
                service_name = booking.service_category.name if booking.service_category else 'Service'
                customer_name = request.user.get_full_name() or request.user.username
                notification = Notification.objects.create(
                    user=provider_user,
                    title='New Booking Request',
                    message=f'You have a new booking request for {service_name} from {customer_name}',
                    notification_type='booking_created',
                    related_id=booking.id
                )
                print(f"✅ Created notification {notification.id} for provider {provider_user.username} about booking {booking.id}")
            except Exception as e:
                # Log error but don't fail the booking creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create notification for booking {booking.id}: {str(e)}")
                print(f"❌ Failed to create notification for booking {booking.id}: {str(e)}")
            
            return Response(
                self.get_serializer(booking).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a booking request (provider only)."""
        booking = self.get_object()
        
        if request.user.role != 'provider':
            return Response(
                {'error': 'Only providers can accept bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            return Response(
                {'error': f'Booking is already {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'accepted'
        booking.accepted_at = timezone.now()
        booking.save()
        
        # Create notification for customer about booking acceptance
        try:
            service_name = booking.service_category.name if booking.service_category else 'Service'
            provider_name = booking.provider.name or booking.provider.user.username
            notification = Notification.objects.create(
                user=booking.customer,
                title='Booking Accepted',
                message=f'Your booking for {service_name} has been accepted by {provider_name}',
                notification_type='booking_accepted',
                related_id=booking.id
            )
            print(f"✅ Created notification {notification.id} for customer {booking.customer.username} about booking acceptance {booking.id}")
        except Exception as e:
            # Log error but don't fail the booking acceptance
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create notification for booking acceptance {booking.id}: {str(e)}")
            print(f"❌ Failed to create notification for booking acceptance {booking.id}: {str(e)}")
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark booking as completed (provider only)."""
        booking = self.get_object()
        
        if request.user.role != 'provider':
            return Response(
                {'error': 'Only providers can complete bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status not in ['accepted', 'in_progress']:
            return Response(
                {'error': f'Cannot complete booking with status {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        booking.save()
        
        # Create notification for customer about booking completion
        try:
            service_name = booking.service_category.name if booking.service_category else 'Service'
            provider_name = booking.provider.name or booking.provider.user.username
            notification = Notification.objects.create(
                user=booking.customer,
                title='Service Completed',
                message=f'Your {service_name} service has been completed by {provider_name}. Please leave a review!',
                notification_type='booking_completed',
                related_id=booking.id
            )
            print(f"✅ Created notification {notification.id} for customer {booking.customer.username} about booking completion {booking.id}")
        except Exception as e:
            # Log error but don't fail the booking completion
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create notification for booking completion {booking.id}: {str(e)}")
            print(f"❌ Failed to create notification for booking completion {booking.id}: {str(e)}")
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking (customer or provider can cancel)."""
        booking = self.get_object()
        
        # Only customer or provider can cancel
        if request.user != booking.customer and request.user != booking.provider.user:
            return Response(
                {'error': 'You do not have permission to cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cannot cancel if already completed or cancelled
        if booking.status == 'completed':
            return Response(
                {'error': 'Cannot cancel a completed booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.status == 'cancelled':
            return Response(
                {'error': 'Booking is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        # Create notification for the other party
        try:
            if request.user == booking.customer:
                # Customer cancelled - notify provider
                service_name = booking.service_category.name if booking.service_category else 'Service'
                customer_name = booking.customer.get_full_name() or booking.customer.username
                notification = Notification.objects.create(
                    user=booking.provider.user,
                    title='Booking Cancelled',
                    message=f'{customer_name} has cancelled the booking for {service_name}',
                    notification_type='booking_cancelled',
                    related_id=booking.id
                )
            else:
                # Provider cancelled - notify customer
                service_name = booking.service_category.name if booking.service_category else 'Service'
                provider_name = booking.provider.name or booking.provider.user.username
                notification = Notification.objects.create(
                    user=booking.customer,
                    title='Booking Cancelled',
                    message=f'{provider_name} has cancelled your booking for {service_name}',
                    notification_type='booking_cancelled',
                    related_id=booking.id
                )
            print(f"✅ Created cancellation notification {notification.id}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create cancellation notification for booking {booking.id}: {str(e)}")
            print(f"❌ Failed to create cancellation notification for booking {booking.id}: {str(e)}")
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get requests for current provider (accepted and pending)."""
        if request.user.role != 'provider':
            return Response(
                {'error': 'Only providers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from providers.models import ServiceProvider
            provider = ServiceProvider.objects.get(user=request.user)
            bookings = Booking.objects.filter(
                provider=provider,
                status__in=['pending', 'accepted', 'in_progress']
            ).order_by('-created_at')
            
            serializer = self.get_serializer(bookings, many=True)
            return Response(serializer.data)
        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Provider profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

