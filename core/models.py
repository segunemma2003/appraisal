from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone


class Department(models.Model):
    """Organizational departments"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Position(models.Model):
    """Staff positions with CONTISS levels"""
    STAFF_LEVEL_CHOICES = [
        ('junior', 'Junior Staff'),
        ('senior', 'Senior Staff'),
    ]
    
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    staff_level = models.CharField(max_length=10, choices=STAFF_LEVEL_CHOICES)
    contiss_level = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.contiss_level}"


class Permission(models.Model):
    """Custom permission model for granular access control"""
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

    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPE_CHOICES)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    department_scope = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_system_permission = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['resource_type', 'permission_type']
        indexes = [
            models.Index(fields=['codename']),
            models.Index(fields=['permission_type', 'resource_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.permission_type}_{self.resource_type}: {self.name}"


class Role(models.Model):
    """Role model for grouping permissions"""
    ROLE_TYPE_CHOICES = [
        ('system', 'System Role'),
        ('department', 'Department Role'),
        ('project', 'Project Role'),
        ('temporary', 'Temporary Role'),
    ]

    name = models.CharField(max_length=200)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPE_CHOICES, default='system')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_system_role = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['codename']),
            models.Index(fields=['role_type', 'department']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """Many-to-many relationship between roles and permissions with conditions"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    conditions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['role', 'permission']
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['permission', 'is_active']),
        ]

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class UserRole(models.Model):
    """User-role assignments with temporal and conditional constraints"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='core_user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='core_user_roles')
    
    # Temporal constraints
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Conditional constraints
    conditions = models.JSONField(default=dict, blank=True)
    
    # Assignment metadata
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='role_assignments')
    reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'role', 'department']
        indexes = [
            models.Index(fields=['user', 'is_active', 'start_date']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['department', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

    @property
    def is_current(self):
        """Check if the role assignment is currently active"""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now and
            (self.end_date is None or self.end_date >= now)
        )


class PermissionOverride(models.Model):
    """Temporary permission overrides for users"""
    OVERRIDE_TYPE_CHOICES = [
        ('grant', 'Grant'),
        ('deny', 'Deny'),
        ('modify', 'Modify'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permission_overrides')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_overrides')
    override_type = models.CharField(max_length=10, choices=OVERRIDE_TYPE_CHOICES)
    
    # Temporal constraints
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Override metadata
    reason = models.TextField()
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='permission_grants')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'permission', 'override_type']
        indexes = [
            models.Index(fields=['user', 'is_active', 'start_date']),
            models.Index(fields=['permission', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.permission.name} ({self.override_type})"

    @property
    def is_current(self):
        """Check if the override is currently active"""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now and
            (self.end_date is None or self.end_date >= now)
        )


class PermissionAudit(models.Model):
    """Audit trail for all permission changes"""
    ACTION_CHOICES = [
        ('granted', 'Permission Granted'),
        ('revoked', 'Permission Revoked'),
        ('modified', 'Permission Modified'),
        ('override_granted', 'Override Granted'),
        ('override_revoked', 'Override Revoked'),
        ('role_assigned', 'Role Assigned'),
        ('role_removed', 'Role Removed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permission_audits')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_audits')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    override = models.ForeignKey(PermissionOverride, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='permission_actions')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['permission', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['performed_by', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.action} {self.permission.name} for {self.user.username} at {self.timestamp}"


class PermissionGroup(models.Model):
    """Groups of permissions for easier management"""
    name = models.CharField(max_length=200)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, related_name='permission_groups')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['codename']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class SystemConfiguration(models.Model):
    """System-wide configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key, default=None):
        """Get configuration value with caching"""
        cache_key = f"config_{key}"
        value = cache.get(cache_key)
        if value is None:
            try:
                config = cls.objects.get(key=key, is_active=True)
                value = config.value
                cache.set(cache_key, value, 3600)  # Cache for 1 hour
            except cls.DoesNotExist:
                value = default
        return value

    @classmethod
    def set_value(cls, key, value, description=""):
        """Set configuration value"""
        config, created = cls.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            config.value = value
            config.description = description
            config.save()
        
        # Clear cache
        cache.delete(f"config_{key}")
        return config


class ApprovalLevel(models.Model):
    """Approval levels for workflows"""
    name = models.CharField(max_length=100)
    level = models.PositiveIntegerField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f"Level {self.level}: {self.name}"


class ApprovalWorkflow(models.Model):
    """Approval workflow definitions"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    approval_levels = models.ManyToManyField(ApprovalLevel, through='ApprovalWorkflowLevel')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ApprovalWorkflowLevel(models.Model):
    """Intermediate model for workflow levels"""
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE)
    approval_level = models.ForeignKey(ApprovalLevel, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ['workflow', 'order']

    def __str__(self):
        return f"{self.workflow.name} - Level {self.order}"


class AuditLog(models.Model):
    """Audit trail for all system changes"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('submit', 'Submit'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} {self.model_name} by {self.user} at {self.timestamp}"
