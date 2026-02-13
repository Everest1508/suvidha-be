from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Review
from .serializers import ReviewSerializer
from bookings.models import Booking


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Custom authentication class that doesn't enforce CSRF for mobile apps."""
    def enforce_csrf(self, request):
        pass


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for review operations."""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]  # Will be customized per action
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def list(self, request):
        """List all reviews, optionally filtered by provider."""
        queryset = Review.objects.all()
        
        provider_id = request.query_params.get('provider', None)
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        # Limit to recent reviews for home page
        limit = request.query_params.get('limit', None)
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_review(self, request):
        """Create a new review. Booking-based: pass booking_id to review a specific completed booking (one review per booking)."""
        if hasattr(request.data, 'copy'):
            data = request.data.copy()
        else:
            data = dict(request.data)
        
        booking_id = data.pop('booking_id', None) or data.pop('booking_id_write', None)
        if booking_id is not None:
            try:
                booking = Booking.objects.get(pk=booking_id)
            except Booking.DoesNotExist:
                return Response(
                    {'error': 'Booking not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if booking.customer_id != request.user.id:
                return Response(
                    {'error': 'You can only review your own bookings.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if booking.status != 'completed':
                return Response(
                    {'error': 'You can only review completed bookings.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Review.objects.filter(booking_id=booking_id).exists():
                return Response(
                    {'error': 'You have already reviewed this booking.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data['booking'] = booking.pk
            data['provider_id'] = booking.provider_id
            data['service_category_id'] = booking.service_category_id
        else:
            if not data.get('provider_id'):
                return Response(
                    {'error': 'provider_id or booking_id is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            review = serializer.save(customer=request.user)
            return Response(self.get_serializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

