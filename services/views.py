from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import ServiceCategory
from .serializers import ServiceCategorySerializer


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing service categories.
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]
