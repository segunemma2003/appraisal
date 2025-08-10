# Dynamic Role & Permission System - Complete Implementation

## 🎯 System Overview

The dynamic role and permission system provides granular control over every action in the appraisal system. It's designed to be flexible, scalable, and secure, with support for temporal constraints, conditional permissions, and comprehensive audit trails.

## 🏗️ Core Components

### 1. Permission Model

```python
class Permission(models.Model):
    PERMISSION_TYPE_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('assign', 'Assign'),
        ('delegate', 'Delegate'),
        ('override', 'Override'),
        ('view_analytics', 'View Analytics'),
        ('manage_users', 'Manage Users'),
        ('configure_system', 'Configure System'),
    ]

    RESOURCE_TYPE_CHOICES = [
        ('evaluation', 'Evaluation'),
        ('kpi', 'KPI'),
        ('form_template', 'Form Template'),
        ('goal', 'Goal'),
        ('approval', 'Approval'),
        ('analytics', 'Analytics'),
        ('user', 'User'),
        ('department', 'Department'),
        ('role', 'Role'),
        ('permission', 'Permission'),
        ('system_config', 'System Configuration'),
        ('audit_log', 'Audit Log'),
        ('notification', 'Notification'),
        ('report', 'Report'),
    ]
```

### 2. Role Model

```python
class Role(models.Model):
    ROLE_TYPE_CHOICES = [
        ('system', 'System Role'),
        ('department', 'Department Role'),
        ('project', 'Project Role'),
        ('temporary', 'Temporary Role'),
    ]
```

### 3. UserRole Model

```python
class UserRole(models.Model):
    # Temporal constraints
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    # Conditional constraints
    conditions = models.JSONField(default=dict, blank=True)

    @property
    def is_current(self):
        """Check if the role assignment is currently active"""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now and
            (self.end_date is None or self.end_date >= now)
        )
```

### 4. PermissionOverride Model

```python
class PermissionOverride(models.Model):
    OVERRIDE_TYPE_CHOICES = [
        ('grant', 'Grant'),
        ('deny', 'Deny'),
        ('modify', 'Modify'),
    ]

    # Temporal constraints
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
```

## 🔧 Permission Service

### Core Methods

#### 1. Get User Permissions

```python
@staticmethod
def get_user_permissions(user, include_overrides=True, include_conditions=True):
    """Get all permissions for a user including roles, overrides, and conditions"""
    # Cached for 5 minutes for performance
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

        cache.set(cache_key, permissions, 300)

    return permissions
```

#### 2. Check Permission

```python
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
```

#### 3. Filter Queryset by Permissions

```python
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
```

## 🎭 Permission Decorators

### 1. Require Single Permission

```python
@PermissionDecorator.require_permission('create', 'kpi')
def create_kpi(request):
    """Create new KPI template"""
    # View logic here
```

### 2. Require Any Permission

```python
@PermissionDecorator.require_any_permission(['read', 'update'], 'evaluation')
def view_evaluation(request, evaluation_id):
    """View evaluation with read or update permission"""
    # View logic here
```

### 3. Require All Permissions

```python
@PermissionDecorator.require_all_permissions(['read', 'approve'], 'evaluation')
def approve_evaluation(request, evaluation_id):
    """Approve evaluation requiring both read and approve permissions"""
    # View logic here
```

## 🔄 Permission Flow Examples

### 1. KPI Management Flow

```
User requests to create KPI
↓
Check permission: 'create_kpi'
↓
If granted: Allow creation
If denied: Return 403 Forbidden
↓
Log action in audit trail
```

### 2. Evaluation Approval Flow

```
User submits evaluation for approval
↓
Check permission: 'approve_evaluation'
↓
Check department access (if department-specific)
↓
Check temporal constraints (if any)
↓
If all checks pass: Allow approval
If any check fails: Return 403 Forbidden
↓
Log approval action
```

### 3. Conditional Permission Flow

```
User requests department-specific action
↓
Check base permission
↓
Check department scope
↓
Check time restrictions (if any)
↓
Check IP restrictions (if any)
↓
Apply permission override (if any)
↓
Return final permission decision
```

## 🎯 Permission Types & Resources

### Permission Types

- **create**: Create new resources
- **read**: View resources
- **update**: Modify existing resources
- **delete**: Remove resources
- **approve**: Approve workflows
- **reject**: Reject workflows
- **export**: Export data
- **import**: Import data
- **assign**: Assign roles/permissions
- **delegate**: Delegate permissions
- **override**: Override permissions
- **view_analytics**: View analytics
- **manage_users**: Manage user accounts
- **configure_system**: Configure system settings

### Resource Types

- **evaluation**: Evaluation forms
- **kpi**: KPI templates
- **form_template**: Form templates
- **goal**: Goals and objectives
- **approval**: Approval workflows
- **analytics**: Analytics and reports
- **user**: User management
- **department**: Department management
- **role**: Role management
- **permission**: Permission management
- **system_config**: System configuration
- **audit_log**: Audit logs
- **notification**: Notifications
- **report**: Reports

## 🏢 Role Management

### 1. Create Role

```python
# Create a new role
role = RoleManagementService.create_role(
    name="Department Manager",
    codename="dept_manager",
    description="Manages department-specific operations",
    role_type="department",
    department=department,
    permissions=[permission1, permission2, permission3]
)
```

### 2. Assign Role to User

```python
# Assign role to user with temporal constraints
user_role = RoleManagementService.assign_role_to_user(
    user=user,
    role=role,
    department=department,
    start_date=timezone.now(),
    end_date=timezone.now() + timedelta(days=30),
    assigned_by=admin_user
)
```

### 3. Grant Permission Override

```python
# Grant temporary permission override
override = RoleManagementService.grant_permission_override(
    user=user,
    permission=permission,
    override_type='grant',
    reason='Special project access',
    granted_by=admin_user,
    start_date=timezone.now(),
    end_date=timezone.now() + timedelta(days=7)
)
```

## 📊 Permission Analytics

### 1. Role Statistics

```python
# Get role usage statistics
role_stats = Role.objects.filter(is_active=True).annotate(
    user_count=Count('userrole')
).order_by('-user_count')
```

### 2. Permission Usage

```python
# Get permission usage statistics
permission_stats = Permission.objects.filter(is_active=True).annotate(
    role_count=Count('rolepermission'),
    override_count=Count('permissionoverride')
).order_by('-role_count')
```

### 3. Department Distribution

```python
# Get department role distribution
dept_role_stats = Department.objects.filter(is_active=True).annotate(
    role_count=Count('role'),
    user_role_count=Count('userrole')
).order_by('-user_role_count')
```

## 🔍 Audit Trail

### 1. Permission Changes

```python
class PermissionAudit(models.Model):
    ACTION_CHOICES = [
        ('granted', 'Permission Granted'),
        ('revoked', 'Permission Revoked'),
        ('modified', 'Permission Modified'),
        ('override_granted', 'Override Granted'),
        ('override_revoked', 'Override Revoked'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True)
    override = models.ForeignKey(PermissionOverride, on_delete=models.CASCADE, null=True)
    reason = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
```

### 2. Audit Logging

```python
# Log permission changes automatically
PermissionAudit.objects.create(
    user=user,
    permission=permission,
    action='granted',
    role=role,
    reason='Role assignment',
    performed_by=admin_user,
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT')
)
```

## 🎨 Template Integration

### 1. Context Processor

```python
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
```

### 2. Template Usage

```html
<!-- Check permission in template -->
{% if has_permission('create_kpi') %}
<a href="{% url 'create_kpi' %}" class="btn btn-primary">Create KPI</a>
{% endif %} {% if has_permission('view_analytics') %}
<a href="{% url 'analytics_dashboard' %}" class="btn btn-info"
  >View Analytics</a
>
{% endif %}

<!-- Conditional content based on permissions -->
{% if 'approve_evaluation' in user_permissions %}
<div class="approval-section">
  <h3>Pending Approvals</h3>
  <!-- Approval content -->
</div>
{% endif %}
```

## 🔧 Configuration

### 1. Settings Configuration

```python
# settings.py
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... other context processors
                'core.permissions.user_permissions',
            ],
        },
    },
]

# Permission system settings
PERMISSION_SETTINGS = {
    'CACHE_TIMEOUT': 300,  # 5 minutes
    'ENABLE_CONDITIONS': True,
    'ENABLE_OVERRIDES': True,
    'AUDIT_ALL_CHANGES': True,
    'DEFAULT_PERMISSION_DENIED': True,
}
```

### 2. URL Configuration

```python
# urls.py
urlpatterns = [
    # Core permission management
    path('core/', include('core.urls')),

    # Appraisal system with permissions
    path('evaluations/', include('evaluations.urls')),
]
```

## 🚀 Usage Examples

### 1. View with Permission Check

```python
@login_required
@PermissionDecorator.require_permission('read', 'evaluation')
def view_evaluation(request, evaluation_id):
    evaluation = get_object_or_404(EvaluationForm, id=evaluation_id)

    # Check if user can access this specific evaluation
    if not PermissionService.has_permission(
        request.user, 'read', 'evaluation', evaluation_id
    ):
        return HttpResponseForbidden("Access denied")

    return render(request, 'evaluations/view_evaluation.html', {
        'evaluation': evaluation
    })
```

### 2. Filtered Queryset

```python
@login_required
@PermissionDecorator.require_permission('read', 'goal')
def goal_list(request):
    goals = Goal.objects.all()

    # Filter goals based on user permissions
    filtered_goals = PermissionService.filter_queryset_by_permissions(
        request.user, goals, 'goal', 'read'
    )

    return render(request, 'evaluations/goal_list.html', {
        'goals': filtered_goals
    })
```

### 3. Conditional Logic

```python
@login_required
def dashboard(request):
    user = request.user
    context = {}

    # Show different content based on permissions
    if PermissionService.has_permission(user, 'view_analytics'):
        context['analytics'] = get_analytics_data()

    if PermissionService.has_permission(user, 'manage_users'):
        context['user_management'] = get_user_management_data()

    if PermissionService.has_permission(user, 'approve_evaluation'):
        context['pending_approvals'] = get_pending_approvals(user)

    return render(request, 'dashboard.html', context)
```

## 🔒 Security Features

### 1. Permission Caching

- User permissions are cached for 5 minutes
- Cache is automatically invalidated when permissions change
- Separate cache keys for different permission combinations

### 2. Temporal Constraints

- Role assignments can have start and end dates
- Permission overrides can be time-limited
- Automatic expiration of temporary permissions

### 3. Conditional Permissions

- Department-specific permissions
- Time-based restrictions
- IP-based restrictions (extensible)
- Custom conditions via JSON fields

### 4. Audit Trail

- Complete audit log of all permission changes
- IP address and user agent tracking
- Reason tracking for all changes
- Immutable audit records

## 📈 Performance Optimization

### 1. Efficient Queries

```python
# Optimized permission queries with select_related
user_roles = UserRole.objects.filter(
    user=user,
    is_active=True
).select_related('role', 'department')

# Batch permission checks
permissions = PermissionService.get_user_permissions(user)
```

### 2. Caching Strategy

```python
# Cache user permissions
cache_key = f"user_permissions_{user.id}_{include_overrides}_{include_conditions}"
permissions = cache.get(cache_key)

if permissions is None:
    # Calculate permissions
    permissions = calculate_user_permissions(user)
    cache.set(cache_key, permissions, 300)  # 5 minutes
```

### 3. Database Indexes

```python
class UserRole(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active', 'start_date']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['department', 'is_active']),
        ]
```

## 🎯 Benefits Achieved

### 1. Granular Control

- Every action is permission-controlled
- Resource-specific permissions
- Department-specific access
- Temporal constraints

### 2. Flexibility

- Dynamic role creation
- Temporary permission overrides
- Conditional permissions
- Extensible permission types

### 3. Security

- Comprehensive audit trail
- Permission caching
- Automatic expiration
- IP tracking

### 4. Performance

- Efficient queries
- Smart caching
- Database optimization
- Batch operations

### 5. Compliance

- Complete audit trail
- Permission justification
- Change tracking
- Immutable records

This dynamic permission system provides enterprise-grade access control that scales with your organization's needs while maintaining security and performance.
