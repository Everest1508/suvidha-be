from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import SavedAddress
from .serializers import SavedAddressSerializer


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Custom authentication class that doesn't enforce CSRF for mobile apps."""
    def enforce_csrf(self, request):
        pass


@method_decorator(csrf_exempt, name='dispatch')
class SavedAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for managing saved addresses"""
    serializer_class = SavedAddressSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get_queryset(self):
        """Return addresses for the current user"""
        return SavedAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user when creating an address"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set an address as default"""
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response(self.get_serializer(address).data)
