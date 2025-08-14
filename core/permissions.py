from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from .models import UserRole, Permission, RolePermission, PermissionOverride
from django.db import models


def get_user_permissions(user):
    """
    Get all permissions for a user based on their roles and overrides.
    Returns a nested dictionary structure for easy permission checking.
    """
    cache_key = f"user_permissions_{user.id}"
    permissions = cache.get(cache_key)
    
    if permissions is None:
        permissions = _build_user_permissions(user)
        cache.set(cache_key, permissions, 300)  # Cache for 5 minutes
    
    return permissions


def _build_user_permissions(user):
    """Build the complete permission structure for a user"""
    permissions = {}
    
    # Get all active role assignments for the user
    user_roles = UserRole.objects.filter(
        user=user,
        is_active=True,
        start_date__lte=timezone.now()
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
    ).select_related('role', 'department')
    
    # Build permissions from roles
    for user_role in user_roles:
        role_permissions = RolePermission.objects.filter(
            role=user_role.role,
            is_active=True
        ).select_related('permission')
        
        for role_perm in role_permissions:
            perm = role_perm.permission
            resource_type = perm.resource_type
            permission_type = perm.permission_type
            
            # Initialize resource type if not exists
            if resource_type not in permissions:
                permissions[resource_type] = {}
            
            # Initialize permission type if not exists
            if permission_type not in permissions[resource_type]:
                permissions[resource_type][permission_type] = []
            
            # Add permission with conditions and scope
            permission_data = {
                'permission_id': perm.id,
                'codename': perm.codename,
                'name': perm.name,
                'conditions': role_perm.conditions,
                'department_scope': user_role.department.id if user_role.department else None,
                'role_id': user_role.role.id,
                'role_name': user_role.role.name,
            }
            
            permissions[resource_type][permission_type].append(permission_data)
    
    # Apply permission overrides
    overrides = PermissionOverride.objects.filter(
        user=user,
        is_active=True,
        start_date__lte=timezone.now()
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
    ).select_related('permission')
    
    for override in overrides:
        perm = override.permission
        resource_type = perm.resource_type
        permission_type = perm.permission_type
        
        if override.override_type == 'deny':
            # Remove permission if it exists
            if resource_type in permissions and permission_type in permissions[resource_type]:
                permissions[resource_type][permission_type] = [
                    p for p in permissions[resource_type][permission_type]
                    if p['permission_id'] != perm.id
                ]
        elif override.override_type == 'grant':
            # Add permission if it doesn't exist
            if resource_type not in permissions:
                permissions[resource_type] = {}
            if permission_type not in permissions[resource_type]:
                permissions[resource_type][permission_type] = []
            
            permission_data = {
                'permission_id': perm.id,
                'codename': perm.codename,
                'name': perm.name,
                'conditions': {},
                'department_scope': None,
                'role_id': None,
                'role_name': 'Override',
                'override_type': 'grant',
            }
            
            permissions[resource_type][permission_type].append(permission_data)
    
    return permissions


def has_permission(user, permission_type, resource_type, **kwargs):
    """
    Check if a user has a specific permission.
    
    Args:
        user: The user to check permissions for
        permission_type: Type of permission (create, read, update, delete, etc.)
        resource_type: Type of resource (user, role, evaluation, etc.)
        **kwargs: Additional context for permission checking
            - department_id: Check department-specific permissions
            - object_id: Check object-specific permissions
            - conditions: Additional conditions to check
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    # Superusers have all permissions
    if user.is_superuser:
        return True
    
    # Get user permissions
    user_permissions = get_user_permissions(user)
    
    # Check if user has the required permission type for the resource
    if resource_type not in user_permissions:
        return False
    
    if permission_type not in user_permissions[resource_type]:
        return False
    
    permissions = user_permissions[resource_type][permission_type]
    
    # Check each permission for the user
    for permission_data in permissions:
        if _check_permission_conditions(permission_data, **kwargs):
            return True
    
    return False


def _check_permission_conditions(permission_data, **kwargs):
    """Check if permission conditions are met"""
    conditions = permission_data.get('conditions', {})
    department_scope = permission_data.get('department_scope')
    
    # Check department scope
    if department_scope is not None:
        requested_department_id = kwargs.get('department_id')
        if requested_department_id != department_scope:
            return False
    
    # Check custom conditions
    for condition_key, condition_value in conditions.items():
        if condition_key in kwargs:
            if kwargs[condition_key] != condition_value:
                return False
        else:
            # If condition is required but not provided, deny permission
            if condition_value is not None:
                return False
    
    return True


def get_user_roles(user):
    """Get all active roles for a user"""
    cache_key = f"user_roles_{user.id}"
    roles = cache.get(cache_key)
    
    if roles is None:
        roles = list(UserRole.objects.filter(
            user=user,
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
        ).select_related('role', 'department'))
        
        cache.set(cache_key, roles, 300)  # Cache for 5 minutes
    
    return roles


def has_role(user, role_codename, department_id=None):
    """Check if user has a specific role"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    user_roles = get_user_roles(user)
    
    for user_role in user_roles:
        if user_role.role.codename == role_codename:
            if department_id is None or user_role.department_id == department_id:
                return True
    
    return False


def get_users_with_permission(permission_type, resource_type, department_id=None):
    """Get all users who have a specific permission"""
    
    # Get all role permissions for this permission type and resource type
    role_permissions = RolePermission.objects.filter(
        permission__permission_type=permission_type,
        permission__resource_type=resource_type,
        is_active=True
    ).select_related('role', 'permission')
    
    # Get users with these roles
    user_ids = set()
    
    for role_perm in role_permissions:
        user_roles = UserRole.objects.filter(
            role=role_perm.role,
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
        )
        
        if department_id is not None:
            user_roles = user_roles.filter(department_id=department_id)
        
        user_ids.update(user_roles.values_list('user_id', flat=True))
    
    # Add users with permission overrides
    overrides = PermissionOverride.objects.filter(
        permission__permission_type=permission_type,
        permission__resource_type=resource_type,
        override_type='grant',
        is_active=True,
        start_date__lte=timezone.now()
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
    )
    
    user_ids.update(overrides.values_list('user_id', flat=True))
    
    # Remove users with deny overrides
    deny_overrides = PermissionOverride.objects.filter(
        permission__permission_type=permission_type,
        permission__resource_type=resource_type,
        override_type='deny',
        is_active=True,
        start_date__lte=timezone.now()
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
    )
    
    denied_user_ids = set(deny_overrides.values_list('user_id', flat=True))
    user_ids = user_ids - denied_user_ids
    
    return User.objects.filter(id__in=user_ids)


def clear_user_permission_cache(user_id):
    """Clear permission cache for a specific user"""
    cache.delete(f"user_permissions_{user_id}")
    cache.delete(f"user_roles_{user_id}")


def clear_all_permission_caches():
    """Clear all permission caches (use sparingly)"""
    # This is a simple approach - in production you might want to use cache versioning
    # or more sophisticated cache invalidation
    pass


# Permission decorators for views
def require_permission(permission_type, resource_type):
    """Decorator to require a specific permission for a view"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, permission_type, resource_type):
                from rest_framework.response import Response
                from rest_framework import status
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role_codename, department_id=None):
    """Decorator to require a specific role for a view"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not has_role(request.user, role_codename, department_id):
                from rest_framework.response import Response
                from rest_framework import status
                return Response({'error': 'Role required'}, status=status.HTTP_403_FORBIDDEN)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Utility functions for common permission checks
def can_manage_users(user, department_id=None):
    """Check if user can manage users"""
    return has_permission(user, 'manage_users', 'user', department_id=department_id)


def can_manage_roles(user, department_id=None):
    """Check if user can manage roles"""
    return has_permission(user, 'create', 'role', department_id=department_id) or \
           has_permission(user, 'update', 'role', department_id=department_id) or \
           has_permission(user, 'delete', 'role', department_id=department_id)


def can_approve_evaluations(user, department_id=None):
    """Check if user can approve evaluations"""
    return has_permission(user, 'approve', 'evaluation', department_id=department_id)


def can_view_analytics(user, department_id=None):
    """Check if user can view analytics"""
    return has_permission(user, 'view_analytics', 'analytics', department_id=department_id)


def can_configure_system(user):
    """Check if user can configure system settings"""
    return has_permission(user, 'configure_system', 'system_config')


def is_hr_user(user):
    """Check if user has HR role"""
    return has_role(user, 'hr')


def is_admin_user(user):
    """Check if user has admin role"""
    return has_role(user, 'admin') or user.is_superuser


def is_supervisor_user(user):
    """Check if user has supervisor role"""
    return has_role(user, 'supervisor')


def get_user_department_scope(user):
    """Get the department scope for a user's permissions"""
    user_roles = get_user_roles(user)
    departments = set()
    
    for user_role in user_roles:
        if user_role.department:
            departments.add(user_role.department.id)
    
    return list(departments) if departments else None 