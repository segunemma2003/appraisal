from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from core.models import Department, Position


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=20, unique=True, default="")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_appointment = models.DateField(null=True, blank=True)
    profile_update_enabled = models.BooleanField(default=False)
    profile_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"


class UserRole(models.Model):
    """User role assignments"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('hr', 'Human Resources'),
        ('supervisor', 'Supervisor'),
        ('staff', 'Staff Member'),
        ('review_panel', 'Review Panel'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'role', 'department']
        ordering = ['user__username', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class SupervisorRelationship(models.Model):
    """Supervisor-subordinate relationships"""
    supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subordinates')
    subordinate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supervisors')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['supervisor', 'subordinate']
        ordering = ['supervisor__username', 'subordinate__username']

    def __str__(self):
        return f"{self.supervisor.username} -> {self.subordinate.username}"


class ProfileUpdateRequest(models.Model):
    """Profile update requests requiring approval"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_update_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_requests_made')
    current_data = models.JSONField(default=dict)
    requested_changes = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='profile_requests_reviewed')
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Profile update request by {self.user.username} - {self.status}"


class StaffQualification(models.Model):
    """Staff qualifications and certifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qualifications')
    qualification_type = models.CharField(max_length=100, default="")
    qualification_name = models.CharField(max_length=200, default="")
    institution = models.CharField(max_length=200, default="")
    date_acquired = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_acquired']

    def __str__(self):
        return f"{self.user.username} - {self.qualification_name}"


class ActingAppointment(models.Model):
    """Acting appointments held by staff"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='acting_appointments')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.user.username} - Acting {self.position.title}"


class StaffTraining(models.Model):
    """Staff training records"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trainings')
    training_name = models.CharField(max_length=200, default="")
    training_type = models.CharField(max_length=100, default="")
    institution = models.CharField(max_length=200, default="")
    start_date = models.DateField()
    end_date = models.DateField()
    duration_hours = models.PositiveIntegerField(default=0)
    certificate_received = models.BooleanField(default=False)
    skills_acquired = models.TextField(blank=True)
    impact_on_work = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.user.username} - {self.training_name}"
