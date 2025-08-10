from django.contrib.auth.models import Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q
from functools import wraps
from typing import List, Dict, Any, Optional, Union
import json

from .models import (
    Permission, Role, UserRole, PermissionOverride, PermissionAudit,
    RolePermission, PermissionGroup, Department
)


class PermissionService:
    """Comprehensive permission service for granular access control"""
    
    @staticmethod
    def get_user_permissions(user, include_overrides=True, include_conditions=True):
        """Get all permissions for a user including roles, overrides, and conditions"""
        if not user.is_authenticated:
            return set()
        
        cache_key = f"user_permissions_{user.id}_{include_overrides}_{include_conditions}"
        permissions = cache.get(cache_key)
        
        if permissions is None:
            permissions = set()
            
            # Get permissions from roles
            user_roles = UserRole.objects.filter(
                user=user,
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__isnull=True
            ).select_related('role', 'department')
            
            for user_role in user_roles:
                if user_role.is_current:
                    role_permissions = PermissionService._get_role_permissions(
                        user_role.role, 
                        user_role.department,
                        include_conditions
                    )
                    permissions.update(role_permissions)
            
            # Get permission overrides
            if include_overrides:
                overrides = PermissionOverride.objects.filter(
                    user=user,
                    is_active=True,
                    start_date__lte=timezone.now(),
                    end_date__isnull=True
                ).select_related('permission')
                
                for override in overrides:
                    if override.is_current:
                        if override.override_type == 'grant':
                            permissions.add(override.permission.codename)
                        elif override.override_type == 'deny':
                            permissions.discard(override.permission.codename)
            
            # Cache for 5 minutes
            cache.set(cache_key, permissions, 300)
        
        return permissions
    
    @staticmethod
    def _get_role_permissions(role, department=None, include_conditions=True):
        """Get permissions for a specific role with conditions"""
        permissions = set()
        
        role_permissions = RolePermission.objects.filter(
            role=role,
            is_active=True
        ).select_related('permission')
        
        for role_permission in role_permissions:
            if include_conditions:
                # Check conditions
                if PermissionService._check_permission_conditions(
                    role_permission.permission,
                    role_permission.conditions,
                    department
                ):
                    permissions.add(role_permission.permission.codename)
            else:
                permissions.add(role_permission.permission.codename)
        
        return permissions
    
    @staticmethod
    def _check_permission_conditions(permission, conditions, department=None):
        """Check if permission conditions are met"""
        if not conditions:
            return True
        
        # Check department scope
        if permission.department_scope and department:
            if permission.department_scope != department:
                return False
        
        # Check time-based conditions
        if 'time_restrictions' in conditions:
            time_restrictions = conditions['time_restrictions']
            current_time = timezone.now().time()
            
            if 'start_time' in time_restrictions:
                if current_time < time_restrictions['start_time']:
                    return False
            
            if 'end_time' in time_restrictions:
                if current_time > time_restrictions['end_time']:
                    return False
        
        # Check day-based conditions
        if 'day_restrictions' in conditions:
            current_weekday = timezone.now().weekday()
            if current_weekday not in conditions['day_restrictions']:
                return False
        
        # Check IP restrictions
        if 'ip_restrictions' in conditions:
            # This would be implemented with request context
            pass
        
        return True
    
    @staticmethod
    def has_permission(user, permission_codename, resource_type=None, resource_id=None, department=None):
        """Check if user has specific permission"""
        if not user.is_authenticated:
            return False
        
        # Get user permissions
        user_permissions = PermissionService.get_user_permissions(user)
        
        # Check for exact permission
        if permission_codename in user_permissions:
            return True
        
        # Check for wildcard permissions
        wildcard_permission = f"{permission_codename}_*"
        if wildcard_permission in user_permissions:
            return True
        
        # Check for resource-specific permissions
        if resource_type and resource_id:
            resource_permission = f"{permission_codename}_{resource_type}_{resource_id}"
            if resource_permission in user_permissions:
                return True
        
        return False
    
    @staticmethod
    def has_any_permission(user, permission_codenames, resource_type=None, resource_id=None):
        """Check if user has any of the specified permissions"""
        for permission_codename in permission_codenames:
            if PermissionService.has_permission(user, permission_codename, resource_type, resource_id):
                return True
        return False
    
    @staticmethod
    def has_all_permissions(user, permission_codenames, resource_type=None, resource_id=None):
        """Check if user has all of the specified permissions"""
        for permission_codename in permission_codenames:
            if not PermissionService.has_permission(user, permission_codename, resource_type, resource_id):
                return False
        return True
    
    @staticmethod
    def get_permissions_for_resource(user, resource_type, resource_id=None):
        """Get all permissions user has for a specific resource"""
        user_permissions = PermissionService.get_user_permissions(user)
        resource_permissions = set()
        
        for permission_codename in user_permissions:
            if permission_codename.startswith(f"*_{resource_type}"):
                resource_permissions.add(permission_codename)
            elif resource_id and permission_codename.startswith(f"*_{resource_type}_{resource_id}"):
                resource_permissions.add(permission_codename)
        
        return resource_permissions
    
    @staticmethod
    def can_access_department_data(user, department):
        """Check if user can access data from a specific department"""
        # Check if user has department-specific permissions
        if PermissionService.has_permission(user, 'read', 'department', department.id):
            return True
        
        # Check if user belongs to the department
        user_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
            department=department
        )
        
        return user_roles.exists()
    
    @staticmethod
    def filter_queryset_by_permissions(user, queryset, resource_type, permission_type='read'):
        """Filter queryset based on user permissions"""
        if not user.is_authenticated:
            return queryset.none()
        
        # Get user's department access
        user_departments = UserRole.objects.filter(
            user=user,
            is_active=True
        ).values_list('department_id', flat=True).distinct()
        
        # Check if user has global access
        if PermissionService.has_permission(user, f"{permission_type}_{resource_type}"):
            return queryset
        
        # Filter by department access
        if user_departments:
            return queryset.filter(department_id__in=user_departments)
        
        return queryset.none()


class PermissionDecorator:
    """Decorator for checking permissions in views"""
    
    @staticmethod
    def require_permission(permission_codename, resource_type=None, resource_id_param=None):
        """Decorator to require specific permission"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                resource_id = None
                if resource_id_param and resource_id_param in kwargs:
                    resource_id = kwargs[resource_id_param]
                
                if not PermissionService.has_permission(
                    request.user, 
                    permission_codename, 
                    resource_type, 
                    resource_id
                ):
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden("Permission denied")
                
                return view_func(request, *args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_any_permission(permission_codenames, resource_type=None, resource_id_param=None):
        """Decorator to require any of the specified permissions"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                resource_id = None
                if resource_id_param and resource_id_param in kwargs:
                    resource_id = kwargs[resource_id_param]
                
                if not PermissionService.has_any_permission(
                    request.user, 
                    permission_codenames, 
                    resource_type, 
                    resource_id
                ):
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden("Permission denied")
                
                return view_func(request, *args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_all_permissions(permission_codenames, resource_type=None, resource_id_param=None):
        """Decorator to require all of the specified permissions"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                resource_id = None
                if resource_id_param and resource_id_param in kwargs:
                    resource_id = kwargs[resource_id_param]
                
                if not PermissionService.has_all_permissions(
                    request.user, 
                    permission_codenames, 
                    resource_type, 
                    resource_id
                ):
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden("Permission denied")
                
                return view_func(request, *args, **kwargs)
            return wrapper
        return decorator


class RoleManagementService:
    """Service for managing roles and permissions"""
    
    @staticmethod
    def create_role(name, codename, description, role_type='system', department=None, permissions=None):
        """Create a new role with permissions"""
        role = Role.objects.create(
            name=name,
            codename=codename,
            description=description,
            role_type=role_type,
            department=department
        )
        
        if permissions:
            for permission in permissions:
                RolePermission.objects.create(
                    role=role,
                    permission=permission
                )
        
        return role
    
    @staticmethod
    def assign_role_to_user(user, role, department=None, start_date=None, end_date=None, assigned_by=None):
        """Assign a role to a user"""
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            department=department,
            start_date=start_date or timezone.now(),
            end_date=end_date,
            assigned_by=assigned_by
        )
        
        # Clear user permission cache
        cache.delete(f"user_permissions_{user.id}_True_True")
        cache.delete(f"user_permissions_{user.id}_True_False")
        cache.delete(f"user_permissions_{user.id}_False_True")
        cache.delete(f"user_permissions_{user.id}_False_False")
        
        return user_role
    
    @staticmethod
    def grant_permission_override(user, permission, override_type, reason, granted_by=None, start_date=None, end_date=None):
        """Grant a temporary permission override"""
        override = PermissionOverride.objects.create(
            user=user,
            permission=permission,
            override_type=override_type,
            reason=reason,
            granted_by=granted_by,
            start_date=start_date or timezone.now(),
            end_date=end_date
        )
        
        # Log the override
        PermissionAudit.objects.create(
            user=user,
            permission=permission,
            action=f"override_{override_type}",
            override=override,
            reason=reason,
            performed_by=granted_by
        )
        
        # Clear user permission cache
        cache.delete(f"user_permissions_{user.id}_True_True")
        cache.delete(f"user_permissions_{user.id}_True_False")
        
        return override
    
    @staticmethod
    def revoke_permission_override(override, revoked_by=None, reason=""):
        """Revoke a permission override"""
        override.is_active = False
        override.save()
        
        # Log the revocation
        PermissionAudit.objects.create(
            user=override.user,
            permission=override.permission,
            action="override_revoked",
            override=override,
            reason=reason,
            performed_by=revoked_by
        )
        
        # Clear user permission cache
        cache.delete(f"user_permissions_{override.user.id}_True_True")
        cache.delete(f"user_permissions_{override.user.id}_True_False")
        
        return override


class PermissionTemplateService:
    """Service for creating permission templates and groups"""
    
    @staticmethod
    def create_system_permissions():
        """Create default system permissions"""
        permissions = []
        
        # Evaluation permissions
        permissions.extend([
            Permission.objects.get_or_create(
                codename='create_evaluation',
                defaults={
                    'name': 'Create Evaluation',
                    'description': 'Can create new evaluation forms',
                    'permission_type': 'create',
                    'resource_type': 'evaluation'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='read_evaluation',
                defaults={
                    'name': 'Read Evaluation',
                    'description': 'Can view evaluation forms',
                    'permission_type': 'read',
                    'resource_type': 'evaluation'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='update_evaluation',
                defaults={
                    'name': 'Update Evaluation',
                    'description': 'Can update evaluation forms',
                    'permission_type': 'update',
                    'resource_type': 'evaluation'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='approve_evaluation',
                defaults={
                    'name': 'Approve Evaluation',
                    'description': 'Can approve evaluation forms',
                    'permission_type': 'approve',
                    'resource_type': 'evaluation'
                }
            )[0],
        ])
        
        # KPI permissions
        permissions.extend([
            Permission.objects.get_or_create(
                codename='create_kpi',
                defaults={
                    'name': 'Create KPI',
                    'description': 'Can create new KPI templates',
                    'permission_type': 'create',
                    'resource_type': 'kpi'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='read_kpi',
                defaults={
                    'name': 'Read KPI',
                    'description': 'Can view KPI templates',
                    'permission_type': 'read',
                    'resource_type': 'kpi'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='update_kpi',
                defaults={
                    'name': 'Update KPI',
                    'description': 'Can update KPI templates',
                    'permission_type': 'update',
                    'resource_type': 'kpi'
                }
            )[0],
        ])
        
        # Goal permissions
        permissions.extend([
            Permission.objects.get_or_create(
                codename='create_goal',
                defaults={
                    'name': 'Create Goal',
                    'description': 'Can create new goals',
                    'permission_type': 'create',
                    'resource_type': 'goal'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='read_goal',
                defaults={
                    'name': 'Read Goal',
                    'description': 'Can view goals',
                    'permission_type': 'read',
                    'resource_type': 'goal'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='update_goal',
                defaults={
                    'name': 'Update Goal',
                    'description': 'Can update goals',
                    'permission_type': 'update',
                    'resource_type': 'goal'
                }
            )[0],
        ])
        
        # Analytics permissions
        permissions.extend([
            Permission.objects.get_or_create(
                codename='view_analytics',
                defaults={
                    'name': 'View Analytics',
                    'description': 'Can view analytics and reports',
                    'permission_type': 'view_analytics',
                    'resource_type': 'analytics'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='export_analytics',
                defaults={
                    'name': 'Export Analytics',
                    'description': 'Can export analytics data',
                    'permission_type': 'export',
                    'resource_type': 'analytics'
                }
            )[0],
        ])
        
        # User management permissions
        permissions.extend([
            Permission.objects.get_or_create(
                codename='manage_users',
                defaults={
                    'name': 'Manage Users',
                    'description': 'Can manage user accounts and roles',
                    'permission_type': 'manage_users',
                    'resource_type': 'user'
                }
            )[0],
            Permission.objects.get_or_create(
                codename='configure_system',
                defaults={
                    'name': 'Configure System',
                    'description': 'Can configure system settings',
                    'permission_type': 'configure_system',
                    'resource_type': 'system_config'
                }
            )[0],
        ])
        
        return permissions
    
    @staticmethod
    def create_default_roles():
        """Create default system roles"""
        # Create permissions first
        permissions = PermissionTemplateService.create_system_permissions()
        
        # Create role-permission mappings
        role_permissions = {
            'staff': [
                'read_evaluation', 'update_evaluation', 'create_goal', 
                'read_goal', 'update_goal'
            ],
            'supervisor': [
                'read_evaluation', 'update_evaluation', 'approve_evaluation',
                'create_goal', 'read_goal', 'update_goal', 'view_analytics'
            ],
            'hr_officer': [
                'create_evaluation', 'read_evaluation', 'update_evaluation',
                'create_kpi', 'read_kpi', 'update_kpi',
                'create_goal', 'read_goal', 'update_goal',
                'view_analytics', 'export_analytics', 'manage_users'
            ],
            'admin': [
                'create_evaluation', 'read_evaluation', 'update_evaluation', 'delete_evaluation',
                'create_kpi', 'read_kpi', 'update_kpi', 'delete_kpi',
                'create_goal', 'read_goal', 'update_goal', 'delete_goal',
                'view_analytics', 'export_analytics', 'manage_users', 'configure_system'
            ]
        }
        
        roles = []
        for role_name, permission_codenames in role_permissions.items():
            role, created = Role.objects.get_or_create(
                codename=role_name,
                defaults={
                    'name': role_name.replace('_', ' ').title(),
                    'description': f'Default {role_name} role',
                    'role_type': 'system',
                    'is_system_role': True
                }
            )
            
            if created:
                # Assign permissions
                for codename in permission_codenames:
                    try:
                        permission = Permission.objects.get(codename=codename)
                        RolePermission.objects.create(role=role, permission=permission)
                    except Permission.DoesNotExist:
                        pass
            
            roles.append(role)
        
        return roles


# Context processor for templates
def user_permissions(request):
    """Add user permissions to template context"""
    if request.user.is_authenticated:
        permissions = PermissionService.get_user_permissions(request.user)
        return {
            'user_permissions': permissions,
            'has_permission': lambda perm: perm in permissions
        }
    return {
        'user_permissions': set(),
        'has_permission': lambda perm: False
    } 