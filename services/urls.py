from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='servicecategory')

urlpatterns = [
    path('', include(router.urls)),
]

