from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('contact/', views.contact_form_submit, name='contact_submit'),
]

