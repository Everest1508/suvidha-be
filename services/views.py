from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication

from providers.models import ServiceProvider
from .models import ServiceCategory
from .serializers import ServiceCategorySerializer


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session auth without CSRF check for mobile app API calls."""
    def enforce_csrf(self, request):
        pass


@method_decorator(csrf_exempt, name='dispatch')
class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing service categories.
    Providers can create a custom category via create_custom action.
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_custom(self, request):
        """
        Allow a provider to create a new service category (e.g. when none exist or they need their own).
        Requires authentication; user must have a provider profile.
        """
        if not ServiceProvider.objects.filter(user=request.user).exists():
            return Response(
                {'error': 'Only providers can create service categories.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response(
                {'error': 'Name is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        description = (request.data.get('description') or '').strip()
        base_slug = slugify(name) or 'category'
        slug = base_slug
        counter = 1
        while ServiceCategory.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1
        # Ensure name is unique
        if ServiceCategory.objects.filter(name__iexact=name).exists():
            return Response(
                {'error': 'A category with this name already exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        category = ServiceCategory.objects.create(
            name=name,
            slug=slug,
            icon=request.data.get('icon') or 'category',
            description=description,
            is_active=True,
        )
        serializer = ServiceCategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
