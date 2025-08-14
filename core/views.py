from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import csv
from io import StringIO

from .models import (
    Department, Position, Permission, Role, RolePermission, 
    UserRole, PermissionOverride, PermissionAudit, PermissionGroup,
    SystemConfiguration, ApprovalLevel, ApprovalWorkflow
)
from .permissions import has_permission, get_user_permissions
from evaluations.models import EvaluationQuestion, KPITemplate, AppraisalFormTemplate
from users.models import UserProfile


# ============================================================================
# ROLE MANAGEMENT APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def role_list(request):
    """List and create roles"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'role'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        roles = Role.objects.filter(is_active=True)
        
        # Filter by department if user has department scope
        user_permissions = get_user_permissions(request.user)
        if not user_permissions.get('role', {}).get('read_all', False):
            user_department = request.user.profile.department
            roles = roles.filter(department=user_department)
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(roles, 20)
        roles_page = paginator.get_page(page)
        
        data = {
            'roles': [{
                'id': role.id,
                'name': role.name,
                'codename': role.codename,
                'description': role.description,
                'role_type': role.role_type,
                'department': role.department.name if role.department else None,
                'is_system_role': role.is_system_role,
                'permissions_count': role.role_permissions.filter(is_active=True).count(),
                'users_count': role.user_roles.filter(is_active=True).count(),
                'created_at': role.created_at,
            } for role in roles_page],
            'total_pages': paginator.num_pages,
            'current_page': page,
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'create', 'role'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                data = request.data
                
                # Validate department scope
                if data.get('department_id'):
                    if not has_permission(request.user, 'create', 'role', department_id=data['department_id']):
                        return Response({'error': 'Permission denied for this department'}, status=status.HTTP_403_FORBIDDEN)
                
                role = Role.objects.create(
                    name=data['name'],
                    codename=data['codename'],
                    description=data.get('description', ''),
                    role_type=data.get('role_type', 'system'),
                    department_id=data.get('department_id'),
                    is_system_role=data.get('is_system_role', False),
                )
                
                # Add permissions if provided
                if data.get('permissions'):
                    for perm_data in data['permissions']:
                        RolePermission.objects.create(
                            role=role,
                            permission_id=perm_data['permission_id'],
                            conditions=perm_data.get('conditions', {}),
                        )
                
                return Response({
                    'id': role.id,
                    'name': role.name,
                    'codename': role.codename,
                    'message': 'Role created successfully'
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def role_detail(request, role_id):
    """Get, update, or delete a specific role"""
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'role'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check department scope
        if role.department and not has_permission(request.user, 'read', 'role', department_id=role.department.id):
            return Response({'error': 'Permission denied for this department'}, status=status.HTTP_403_FORBIDDEN)
        
        permissions = role.role_permissions.filter(is_active=True).select_related('permission')
        users = role.user_roles.filter(is_active=True).select_related('user')
        
        data = {
            'id': role.id,
            'name': role.name,
            'codename': role.codename,
            'description': role.description,
            'role_type': role.role_type,
            'department': {
                'id': role.department.id,
                'name': role.department.name
            } if role.department else None,
            'is_system_role': role.is_system_role,
            'permissions': [{
                'id': rp.permission.id,
                'name': rp.permission.name,
                'codename': rp.permission.codename,
                'permission_type': rp.permission.permission_type,
                'resource_type': rp.permission.resource_type,
                'conditions': rp.conditions,
            } for rp in permissions],
            'users': [{
                'id': ur.user.id,
                'username': ur.user.username,
                'email': ur.user.email,
                'start_date': ur.start_date,
                'end_date': ur.end_date,
                'is_current': ur.is_current,
            } for ur in users],
            'created_at': role.created_at,
            'updated_at': role.updated_at,
        }
        
        return Response(data)
    
    elif request.method == 'PUT':
        if not has_permission(request.user, 'update', 'role'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                data = request.data
                
                # Update role fields
                if 'name' in data:
                    role.name = data['name']
                if 'description' in data:
                    role.description = data['description']
                if 'role_type' in data:
                    role.role_type = data['role_type']
                if 'department_id' in data:
                    role.department_id = data['department_id']
                
                role.save()
                
                # Update permissions if provided
                if 'permissions' in data:
                    # Remove existing permissions
                    role.role_permissions.filter(is_active=True).delete()
                    
                    # Add new permissions
                    for perm_data in data['permissions']:
                        RolePermission.objects.create(
                            role=role,
                            permission_id=perm_data['permission_id'],
                            conditions=perm_data.get('conditions', {}),
                        )
                
                return Response({'message': 'Role updated successfully'})
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not has_permission(request.user, 'delete', 'role'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if role is in use
        if role.user_roles.filter(is_active=True).exists():
            return Response({'error': 'Cannot delete role that is assigned to users'}, status=status.HTTP_400_BAD_REQUEST)
        
        role.is_active = False
        role.save()
        
        return Response({'message': 'Role deleted successfully'})


# ============================================================================
# PERMISSION MANAGEMENT APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def permission_list(request):
    """List and create permissions"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'permission'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        permissions = Permission.objects.filter(is_active=True)
        
        # Filter by resource type
        resource_type = request.GET.get('resource_type')
        if resource_type:
            permissions = permissions.filter(resource_type=resource_type)
        
        # Filter by permission type
        permission_type = request.GET.get('permission_type')
        if permission_type:
            permissions = permissions.filter(permission_type=permission_type)
        
        data = {
            'permissions': [{
                'id': perm.id,
                'codename': perm.codename,
                'name': perm.name,
                'description': perm.description,
                'permission_type': perm.permission_type,
                'resource_type': perm.resource_type,
                'department_scope': perm.department_scope.name if perm.department_scope else None,
                'is_system_permission': perm.is_system_permission,
                'roles_count': perm.role_permissions.filter(is_active=True).count(),
                'created_at': perm.created_at,
            } for perm in permissions]
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'create', 'permission'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                data = request.data
                
                permission = Permission.objects.create(
                    codename=data['codename'],
                    name=data['name'],
                    description=data.get('description', ''),
                    permission_type=data['permission_type'],
                    resource_type=data['resource_type'],
                    department_scope_id=data.get('department_scope_id'),
                    is_system_permission=data.get('is_system_permission', False),
                )
                
                return Response({
                    'id': permission.id,
                    'codename': permission.codename,
                    'name': permission.name,
                    'message': 'Permission created successfully'
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permission_choices(request):
    """Get available permission and resource type choices"""
    data = {
        'permission_types': Permission.PERMISSION_TYPE_CHOICES,
        'resource_types': Permission.RESOURCE_TYPE_CHOICES,
        'role_types': Role.ROLE_TYPE_CHOICES,
    }
    return Response(data)


# ============================================================================
# USER ROLE ASSIGNMENT APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_role_list(request):
    """List and create user role assignments"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'user'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        user_roles = UserRole.objects.filter(is_active=True).select_related('user', 'role', 'department')
        
        # Filter by user
        user_id = request.GET.get('user_id')
        if user_id:
            user_roles = user_roles.filter(user_id=user_id)
        
        # Filter by role
        role_id = request.GET.get('role_id')
        if role_id:
            user_roles = user_roles.filter(role_id=role_id)
        
        # Filter by department
        department_id = request.GET.get('department_id')
        if department_id:
            user_roles = user_roles.filter(department_id=department_id)
        
        data = {
            'user_roles': [{
                'id': ur.id,
                'user': {
                    'id': ur.user.id,
                    'username': ur.user.username,
                    'email': ur.user.email,
                },
                'role': {
                    'id': ur.role.id,
                    'name': ur.role.name,
                    'codename': ur.role.codename,
                },
                'department': {
                    'id': ur.department.id,
                    'name': ur.department.name,
                } if ur.department else None,
                'start_date': ur.start_date,
                'end_date': ur.end_date,
                'is_current': ur.is_current,
                'assigned_by': ur.assigned_by.username if ur.assigned_by else None,
                'reason': ur.reason,
            } for ur in user_roles]
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'assign', 'user'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                data = request.data
                
                # Validate user exists
                user = get_object_or_404(User, id=data['user_id'])
                
                # Validate role exists
                role = get_object_or_404(Role, id=data['role_id'])
                
                # Check if assignment already exists
                existing = UserRole.objects.filter(
                    user=user,
                    role=role,
                    department_id=data.get('department_id'),
                    is_active=True
                ).first()
                
                if existing:
                    return Response({'error': 'User already has this role assignment'}, status=status.HTTP_400_BAD_REQUEST)
                
                user_role = UserRole.objects.create(
                    user=user,
                    role=role,
                    department_id=data.get('department_id'),
                    start_date=data.get('start_date', timezone.now()),
                    end_date=data.get('end_date'),
                    conditions=data.get('conditions', {}),
                    assigned_by=request.user,
                    reason=data.get('reason', ''),
                )
                
                return Response({
                    'id': user_role.id,
                    'message': 'Role assigned successfully'
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_role_detail(request, user_role_id):
    """Remove a user role assignment"""
    if not has_permission(request.user, 'assign', 'user'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    user_role = get_object_or_404(UserRole, id=user_role_id)
    user_role.is_active = False
    user_role.save()
    
    return Response({'message': 'Role assignment removed successfully'})


# ============================================================================
# BULK USER REGISTRATION APIs
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_user_registration(request):
    """Bulk register users from CSV or JSON data"""
    if not has_permission(request.user, 'create', 'user'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        with transaction.atomic():
            data = request.data
            users_data = data.get('users', [])
            
            if not users_data:
                return Response({'error': 'No users data provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_users = []
            errors = []
            
            for user_data in users_data:
                try:
                    # Create user
                    user = User.objects.create_user(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data.get('password', 'defaultpassword123'),
                        first_name=user_data.get('first_name', ''),
                        last_name=user_data.get('last_name', ''),
                    )
                    
                    # Create user profile
                    profile = UserProfile.objects.create(
                        user=user,
                        department_id=user_data.get('department_id'),
                        position_id=user_data.get('position_id'),
                        employee_id=user_data.get('employee_id', ''),
                        phone_number=user_data.get('phone_number', ''),
                        date_of_birth=user_data.get('date_of_birth'),
                        hire_date=user_data.get('hire_date'),
                        supervisor_id=user_data.get('supervisor_id'),
                    )
                    
                    # Assign roles if provided
                    if user_data.get('roles'):
                        for role_data in user_data['roles']:
                            UserRole.objects.create(
                                user=user,
                                role_id=role_data['role_id'],
                                department_id=role_data.get('department_id'),
                                start_date=role_data.get('start_date', timezone.now()),
                                end_date=role_data.get('end_date'),
                                assigned_by=request.user,
                                reason=role_data.get('reason', 'Bulk registration'),
                            )
                    
                    created_users.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'employee_id': profile.employee_id,
                    })
                    
                except Exception as e:
                    errors.append({
                        'username': user_data.get('username', 'Unknown'),
                        'error': str(e)
                    })
            
            return Response({
                'created_users': created_users,
                'errors': errors,
                'total_created': len(created_users),
                'total_errors': len(errors),
                'message': f'Successfully created {len(created_users)} users'
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_user_registration_csv(request):
    """Bulk register users from CSV file"""
    if not has_permission(request.user, 'create', 'user'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return Response({'error': 'No CSV file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read CSV file
        csv_data = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))
        
        users_data = []
        for row in csv_reader:
            users_data.append({
                'username': row['username'],
                'email': row['email'],
                'first_name': row.get('first_name', ''),
                'last_name': row.get('last_name', ''),
                'password': row.get('password', 'defaultpassword123'),
                'department_id': row.get('department_id'),
                'position_id': row.get('position_id'),
                'employee_id': row.get('employee_id', ''),
                'phone_number': row.get('phone_number', ''),
                'supervisor_id': row.get('supervisor_id'),
            })
        
        # Use the existing bulk registration logic
        request.data = {'users': users_data}
        return bulk_user_registration(request)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# SYSTEM CONFIGURATION APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def system_config_list(request):
    """List and create system configurations"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'system_config'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        configs = SystemConfiguration.objects.filter(is_active=True)
        
        data = {
            'configurations': [{
                'key': config.key,
                'value': config.value,
                'description': config.description,
                'created_at': config.created_at,
                'updated_at': config.updated_at,
            } for config in configs]
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'create', 'system_config'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            data = request.data
            config = SystemConfiguration.set_value(
                key=data['key'],
                value=data['value'],
                description=data.get('description', '')
            )
            
            return Response({
                'key': config.key,
                'value': config.value,
                'message': 'Configuration created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def system_config_detail(request, key):
    """Get or update a specific system configuration"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'system_config'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        value = SystemConfiguration.get_value(key)
        if value is None:
            return Response({'error': 'Configuration not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'key': key, 'value': value})
    
    elif request.method == 'PUT':
        if not has_permission(request.user, 'update', 'system_config'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            data = request.data
            config = SystemConfiguration.set_value(
                key=key,
                value=data['value'],
                description=data.get('description', '')
            )
            
            return Response({
                'key': config.key,
                'value': config.value,
                'message': 'Configuration updated successfully'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
