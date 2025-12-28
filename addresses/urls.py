from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SavedAddressViewSet

router = DefaultRouter()
router.register(r'', SavedAddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]

