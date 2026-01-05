from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('contact/', views.contact_form_submit, name='contact_submit'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('about-us/', views.about_us, name='about_us'),
]

