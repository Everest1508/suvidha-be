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
import requests
import json
from django.conf import settings
import os
from pathlib import Path


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
                # Push notification will be sent automatically via signal
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
    def start_negotiation(self, request, pk=None):
        """Start negotiation for a booking (provider only)."""
        booking = self.get_object()
        
        if request.user.role != 'provider':
            return Response(
                {'error': 'Only providers can start negotiation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            return Response(
                {'error': f'Cannot start negotiation. Current status: {booking.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'negotiation'
        booking.save()
        
        # Create notification for customer
        try:
            customer_name = booking.customer.get_full_name() or booking.customer.username
            service_name = booking.service_category.name if booking.service_category else 'Service'
            notification = Notification.objects.create(
                user=booking.customer,
                title='Negotiation Started',
                message=f'Provider has started negotiation for {service_name}. You can now chat to discuss details.',
                notification_type='booking_negotiation',
                related_id=booking.id
            )
            print(f"✅ Created notification {notification.id} for customer {booking.customer.username} about negotiation {booking.id}")
        except Exception as e:
            print(f"❌ Failed to create notification: {str(e)}")
        
        return Response(
            self.get_serializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a booking request (provider only)."""
        booking = self.get_object()
        
        if request.user.role != 'provider':
            return Response(
                {'error': 'Only providers can accept bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status not in ['pending', 'negotiation']:
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
        """Mark booking as completed and automatically deduct payment from customer wallet (provider only)."""
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
        
        # Check if price is set
        if not booking.price:
            return Response(
                {'error': 'Booking price is not set. Cannot complete booking.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Automatically deduct money from customer wallet and add to provider wallet
        try:
            from accounts.models import Wallet, WalletTransaction
            from django.db import transaction as db_transaction
            from decimal import Decimal
            
            with db_transaction.atomic():
                # Get or create wallets
                customer_wallet, _ = Wallet.objects.get_or_create(user=booking.customer)
                provider_wallet, _ = Wallet.objects.get_or_create(user=booking.provider.user)
                
                # Check if customer has sufficient balance
                if customer_wallet.balance < booking.price:
                    return Response(
                        {'error': f'Customer has insufficient wallet balance. Balance: Rs. {customer_wallet.balance}/-, Required: Rs. {booking.price}/-'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Deduct from customer wallet
                customer_wallet.deduct_money(booking.price)
                WalletTransaction.objects.create(
                    wallet=customer_wallet,
                    transaction_type='payment',
                    amount=booking.price,
                    description=f'Payment for completed booking #{booking.id}',
                    related_booking=booking
                )
                
                # Add to provider wallet
                provider_wallet.add_money(booking.price)
                WalletTransaction.objects.create(
                    wallet=provider_wallet,
                    transaction_type='received',
                    amount=booking.price,
                    description=f'Payment received for completed booking #{booking.id}',
                    related_booking=booking
                )
                
                # Update booking status
                booking.status = 'payment'
                booking.completed_at = timezone.now()
                booking.save()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to process payment for booking {booking.id}: {str(e)}")
            print(f"❌ Failed to process payment for booking {booking.id}: {str(e)}")
            return Response(
                {'error': f'Failed to process payment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create notification for customer about booking completion
        try:
            service_name = booking.service_category.name if booking.service_category else 'Service'
            provider_name = booking.provider.name or booking.provider.user.username
            notification = Notification.objects.create(
                user=booking.customer,
                title='Service Completed',
                message=f'Your {service_name} service has been completed by {provider_name}. Payment of Rs. {booking.price}/- has been deducted from your wallet. Please leave a review!',
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
        
        # Create notification for provider about payment received
        try:
            service_name = booking.service_category.name if booking.service_category else 'Service'
            customer_name = booking.customer.get_full_name() or booking.customer.username
            notification = Notification.objects.create(
                user=booking.provider.user,
                title='Payment Received',
                message=f'You have received Rs. {booking.price}/- from {customer_name} for {service_name}.',
                notification_type='payment_received',
                related_id=booking.id
            )
            print(f"✅ Created notification {notification.id} for provider {booking.provider.user.username} about payment {booking.id}")
        except Exception as e:
            print(f"❌ Failed to create payment notification: {str(e)}")
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a booking during negotiation (customer or provider can reject)."""
        booking = self.get_object()
        
        # Only customer or provider can reject
        if request.user != booking.customer and request.user != booking.provider.user:
            return Response(
                {'error': 'You do not have permission to reject this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Can only reject during negotiation
        if booking.status != 'negotiation':
            return Response(
                {'error': f'Can only reject during negotiation. Current status: {booking.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        # Create notification for the other party
        try:
            other_user = booking.customer if request.user == booking.provider.user else booking.provider.user
            service_name = booking.service_category.name if booking.service_category else 'Service'
            notification = Notification.objects.create(
                user=other_user,
                title='Booking Rejected',
                message=f'Booking for {service_name} has been rejected during negotiation.',
                notification_type='booking_cancelled',
                related_id=booking.id
            )
            print(f"✅ Created notification {notification.id} for user {other_user.username} about rejection {booking.id}")
        except Exception as e:
            print(f"❌ Failed to create notification: {str(e)}")
        
        return Response(
            self.get_serializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def propose_price(self, request, pk=None):
        """Propose a new price during negotiation (both customer and provider can propose)."""
        booking = self.get_object()
        
        # Only customer or provider can propose
        if request.user != booking.customer and request.user != booking.provider.user:
            return Response(
                {'error': 'Only the customer or provider can propose a price'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'negotiation':
            return Response(
                {'error': f'Can only propose price during negotiation. Current status: {booking.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.price_locked:
            return Response(
                {'error': 'Price is already locked and cannot be changed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proposed_price = request.data.get('price')
        if not proposed_price:
            return Response(
                {'error': 'price is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            price_decimal = float(proposed_price)
            if price_decimal <= 0:
                return Response(
                    {'error': 'Price must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid price format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.proposed_price = price_decimal
        booking.proposed_by = request.user
        booking.save()
        
        # Create notification for the other party
        try:
            other_user = booking.customer if request.user == booking.provider.user else booking.provider.user
            service_name = booking.service_category.name if booking.service_category else 'Service'
            proposer_name = request.user.get_full_name() or request.user.username
            notification = Notification.objects.create(
                user=other_user,
                title='New Price Proposed',
                message=f'{proposer_name} has proposed a price of Rs. {price_decimal}/- for {service_name}. You can accept or propose a different price.',
                notification_type='booking_negotiation',
                related_id=booking.id
            )
            print(f"✅ Created notification {notification.id} for user {other_user.username} about price proposal {booking.id}")
        except Exception as e:
            print(f"❌ Failed to create notification: {str(e)}")
        
        return Response(
            self.get_serializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def accept_price(self, request, pk=None):
        """Accept the proposed price and move to accepted status (both parties can accept)."""
        booking = self.get_object()
        
        # Only customer or provider can accept
        if request.user != booking.customer and request.user != booking.provider.user:
            return Response(
                {'error': 'Only the customer or provider can accept the price'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'negotiation':
            return Response(
                {'error': f'Can only accept price during negotiation. Current status: {booking.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not booking.proposed_price:
            return Response(
                {'error': 'No price has been proposed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lock the price and move to accepted
        booking.price = booking.proposed_price
        booking.price_locked = True
        booking.status = 'accepted'
        booking.accepted_at = timezone.now()
        booking.save()
        
        # Create notification for the other party
        try:
            other_user = booking.customer if request.user == booking.provider.user else booking.provider.user
            service_name = booking.service_category.name if booking.service_category else 'Service'
            accepter_name = request.user.get_full_name() or request.user.username
            notification = Notification.objects.create(
                user=other_user,
                title='Price Accepted',
                message=f'{accepter_name} has accepted the price of Rs. {booking.price}/- for {service_name}. Booking is now accepted.',
                notification_type='booking_accepted',
                related_id=booking.id
            )
            print(f"✅ Created notification {notification.id} for user {other_user.username} about price acceptance {booking.id}")
        except Exception as e:
            print(f"❌ Failed to create notification: {str(e)}")
        
        return Response(
            self.get_serializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking (customer or provider can cancel in negotiation or accepted states)."""
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
        
        # Can cancel in pending, negotiation, accepted, in_progress, or payment states
        if booking.status not in ['pending', 'negotiation', 'accepted', 'in_progress', 'payment']:
            return Response(
                {'error': f'Can only cancel bookings in pending, negotiation, accepted, in_progress, or payment states. Current status: {booking.get_status_display()}'},
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
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """Pay for completed booking (customer only)."""
        booking = self.get_object()
        
        if request.user != booking.customer:
            return Response(
                {'error': 'Only the customer can pay for this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'payment':
            return Response(
                {'error': f'Booking is not ready for payment. Current status: {booking.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not booking.price:
            return Response(
                {'error': 'Booking price is not set'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get customer wallet
        from accounts.models import Wallet, WalletTransaction
        customer_wallet, _ = Wallet.objects.get_or_create(user=booking.customer)
        
        # Check if customer has sufficient balance
        if customer_wallet.balance < booking.price:
            return Response(
                {'error': 'Insufficient wallet balance. Please add money to your wallet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get provider wallet
        provider_wallet, _ = Wallet.objects.get_or_create(user=booking.provider.user)
        
        # Process payment
        from django.db import transaction as db_transaction
        from decimal import Decimal
        with db_transaction.atomic():
            # Deduct from customer wallet
            customer_wallet.deduct_money(booking.price)
            WalletTransaction.objects.create(
                wallet=customer_wallet,
                transaction_type='payment',
                amount=booking.price,
                description=f'Payment for booking #{booking.id}',
                related_booking=booking
            )
            
            # Add to provider wallet
            provider_wallet.add_money(booking.price)
            WalletTransaction.objects.create(
                wallet=provider_wallet,
                transaction_type='received',
                amount=booking.price,
                description=f'Payment received for booking #{booking.id}',
                related_booking=booking
            )
            
            # Update booking status to completed
            booking.status = 'completed'
            booking.save()
        
        # Create notification for provider
        try:
            service_name = booking.service_category.name if booking.service_category else 'Service'
            customer_name = booking.customer.get_full_name() or booking.customer.username
            notification = Notification.objects.create(
                user=booking.provider.user,
                title='Payment Received',
                message=f'You have received Rs. {booking.price}/- from {customer_name} for {service_name}.',
                notification_type='payment_received',
                related_id=booking.id
            )
            print(f"✅ Created notification {notification.id} for provider {booking.provider.user.username} about payment {booking.id}")
        except Exception as e:
            print(f"❌ Failed to create notification: {str(e)}")
        
        return Response(
            self.get_serializer(booking).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get requests for current provider (pending, negotiation, accepted, and in_progress)."""
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
                status__in=['pending', 'negotiation', 'accepted', 'in_progress']
            ).order_by('-created_at')
            
            serializer = self.get_serializer(bookings, many=True)
            return Response(serializer.data)
        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Provider profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# Push notifications are now handled automatically via Django signals
# See: notifications/signals.py
# The signal automatically sends push notifications when a Notification is created

