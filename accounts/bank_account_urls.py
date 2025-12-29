from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BankAccountViewSet

router = DefaultRouter()
router.register(r'', BankAccountViewSet, basename='bankaccount')

urlpatterns = [
    path('', include(router.urls)),
]

