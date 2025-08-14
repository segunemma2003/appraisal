from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ============================================================================
    # ROLE MANAGEMENT URLs
    # ============================================================================
    path('roles/', views.role_list, name='role_list'),
    path('roles/<int:role_id>/', views.role_detail, name='role_detail'),
    
    # ============================================================================
    # PERMISSION MANAGEMENT URLs
    # ============================================================================
    path('permissions/', views.permission_list, name='permission_list'),
    path('permissions/choices/', views.permission_choices, name='permission_choices'),
    
    # ============================================================================
    # USER ROLE ASSIGNMENT URLs
    # ============================================================================
    path('user-roles/', views.user_role_list, name='user_role_list'),
    path('user-roles/<int:user_role_id>/', views.user_role_detail, name='user_role_detail'),
    
    # ============================================================================
    # BULK USER REGISTRATION URLs
    # ============================================================================
    path('bulk-register/', views.bulk_user_registration, name='bulk_user_registration'),
    path('bulk-register-csv/', views.bulk_user_registration_csv, name='bulk_user_registration_csv'),
    
    # ============================================================================
    # SYSTEM CONFIGURATION URLs
    # ============================================================================
    path('config/', views.system_config_list, name='system_config_list'),
    path('config/<str:key>/', views.system_config_detail, name='system_config_detail'),
] 