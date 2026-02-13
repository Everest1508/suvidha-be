from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('', views.dashboard, name='dashboard'),
    path('logout/', views.admin_logout, name='logout'),
    path('users/', views.users_list, name='users_list'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('providers/', views.providers_list, name='providers_list'),
    path('providers/<int:provider_id>/', views.provider_detail, name='provider_detail'),
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('tickets/', views.tickets_list, name='tickets_list'),
    path('email-settings/', views.email_settings, name='email_settings'),
]

