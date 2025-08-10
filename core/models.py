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
