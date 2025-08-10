from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Role Management
    path('roles/', views.role_management, name='role_management'),
    path('roles/create/', views.create_role, name='create_role'),
    path('roles/<int:role_id>/edit/', views.edit_role, name='edit_role'),
    
    # Dynamic Role Request System
    path('request-role/', views.request_role, name='request_role'),
    path('available-roles/', views.available_roles, name='available_roles'),
    path('my-role-requests/', views.my_role_requests, name='my_role_requests'),
    path('role-requests/<int:request_id>/', views.role_request_detail, name='role_request_detail'),
    path('role-requests/<int:request_id>/comment/', views.add_role_request_comment, name='add_role_request_comment'),
    path('role-requests/<int:request_id>/cancel/', views.cancel_role_request, name='cancel_role_request'),
    
    # Admin Role Request Management
    path('pending-role-requests/', views.pending_role_requests, name='pending_role_requests'),
    path('approve-role-request/<int:request_id>/', views.approve_role_request, name='approve_role_request'),
    
    # Permission Management
    path('permissions/', views.permission_management, name='permission_management'),
    path('permissions/create/', views.create_permission, name='create_permission'),
    
    # User Role Management
    path('user-roles/', views.user_role_management, name='user_role_management'),
    path('user-roles/assign/', views.assign_role_to_user, name='assign_role_to_user'),
    
    # Permission Override Management
    path('permission-overrides/', views.permission_override_management, name='permission_override_management'),
    path('permission-overrides/grant/', views.grant_permission_override, name='grant_permission_override'),
    
    # Audit and Analytics
    path('permission-audit/', views.permission_audit_log, name='permission_audit_log'),
    path('permission-analytics/', views.permission_analytics, name='permission_analytics'),
    
    # System Initialization
    path('initialize-system/', views.initialize_system_permissions, name='initialize_system_permissions'),
    
    # API Endpoints
    path('api/check-permissions/', views.check_user_permissions, name='check_user_permissions'),
    path('api/get-user-permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('api/revoke-override/', views.revoke_override, name='revoke_override'),
    path('api/deactivate-user-role/', views.deactivate_user_role, name='deactivate_user_role'),
] 