from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from core.models import Department, ApprovalLevel, ApprovalWorkflow
from users.models import UserProfile


class EvaluationPeriod(models.Model):
    """Evaluation periods and timeframes"""
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    submission_deadline = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_open_for_submission = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class KPITemplate(models.Model):
    """Dynamic KPI templates that can be reused and customized"""
    KPI_TYPE_CHOICES = [
        ('quantitative', 'Quantitative'),
        ('qualitative', 'Qualitative'),
        ('percentage', 'Percentage'),
        ('currency', 'Currency'),
        ('boolean', 'Yes/No'),
    ]
    
    VISIBILITY_CHOICES = [
        ('all', 'All Staff'),
        ('management', 'Management Only'),
        ('hr', 'HR Only'),
        ('department', 'Department Specific'),
        ('role', 'Role Specific'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    kpi_type = models.CharField(max_length=20, choices=KPI_TYPE_CHOICES)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='all')
    target_departments = models.ManyToManyField(Department, blank=True)
    target_roles = models.JSONField(default=list, blank=True)  # List of role names
    unit_of_measure = models.CharField(max_length=50, blank=True)  # e.g., "sales", "hours", "%"
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    default_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    is_auto_calculated = models.BooleanField(default=False)
    data_source = models.CharField(max_length=100, blank=True)  # Integration source
    calculation_formula = models.TextField(blank=True)  # For auto-calculated KPIs
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'version']

    def __str__(self):
        return f"{self.name} (v{self.version})"


class AppraisalFormTemplate(models.Model):
    """Dynamic appraisal form templates"""
    FORM_TYPE_CHOICES = [
        ('annual', 'Annual Review'),
        ('probation', 'Probation Review'),
        ('promotion', 'Promotion Review'),
        ('quarterly', 'Quarterly Review'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES)
    target_departments = models.ManyToManyField(Department, blank=True)
    target_staff_levels = models.JSONField(default=list, blank=True)
    kpis = models.ManyToManyField(KPITemplate, through='FormKPI')
    approval_workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'version']

    def __str__(self):
        return f"{self.name} (v{self.version})"


class FormKPI(models.Model):
    """Intermediate model for form-KPI relationships with weights"""
    form_template = models.ForeignKey(AppraisalFormTemplate, on_delete=models.CASCADE)
    kpi = models.ForeignKey(KPITemplate, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    is_required = models.BooleanField(default=True)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['form_template', 'kpi']
        ordering = ['order']

    def __str__(self):
        return f"{self.form_template.name} - {self.kpi.name}"


class ConditionalApprovalRule(models.Model):
    """Rules for conditional approval triggers"""
    CONDITION_TYPE_CHOICES = [
        ('score_threshold', 'Score Threshold'),
        ('kpi_failure', 'KPI Failure'),
        ('department', 'Department Specific'),
        ('role', 'Role Specific'),
        ('custom', 'Custom Condition'),
    ]
    
    ACTION_CHOICES = [
        ('add_approver', 'Add Approver'),
        ('escalate', 'Escalate to Higher Level'),
        ('notify_hr', 'Notify HR'),
        ('require_improvement_plan', 'Require Improvement Plan'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPE_CHOICES)
    condition_parameters = models.JSONField()  # Flexible condition parameters
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    action_parameters = models.JSONField()  # Action-specific parameters
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.get_action_display()}"


class Goal(models.Model):
    """Individual and team goals for tracking progress"""
    GOAL_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('team', 'Team'),
        ('department', 'Department'),
        ('company', 'Company'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_goals')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_goals')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    target_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    kpi_target = models.ForeignKey(KPITemplate, on_delete=models.SET_NULL, null=True, blank=True)
    target_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-target_date']

    def __str__(self):
        return f"{self.title} - {self.assigned_to.username}"


class GoalProgress(models.Model):
    """Goal progress tracking over time"""
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='progress_updates')
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.goal.title} - {self.progress_percentage}%"


class PeerFeedback(models.Model):
    """Anonymous peer feedback for 360-degree evaluations"""
    evaluation_form = models.ForeignKey('EvaluationForm', on_delete=models.CASCADE, related_name='peer_feedback')
    feedback_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='provided_feedback')
    feedback_recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedback')
    feedback_data = models.JSONField()  # Structured feedback data
    is_anonymous = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['evaluation_form', 'feedback_provider', 'feedback_recipient']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Feedback from {self.feedback_provider.username} to {self.feedback_recipient.username}"


class EvaluationQuestion(models.Model):
    """Dynamic evaluation questions"""
    STAFF_LEVEL_CHOICES = [
        ('junior', 'Junior Staff'),
        ('senior', 'Senior Staff'),
    ]
    
    SECTION_CHOICES = [
        ('personal_data', 'Personal Data'),
        ('qualifications', 'Qualifications'),
        ('training', 'Training'),
        ('responsibilities', 'Responsibilities'),
        ('challenges', 'Challenges'),
        ('goals', 'Goals'),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('textarea', 'Text Area'),
        ('select', 'Select'),
        ('date', 'Date'),
        ('number', 'Number'),
    ]
    
    question_text = models.CharField(max_length=500)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    staff_level = models.CharField(max_length=10, choices=STAFF_LEVEL_CHOICES)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    options = models.TextField(blank=True)  # For select questions
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['staff_level', 'section', 'order']
        unique_together = ['section', 'staff_level', 'order']

    def __str__(self):
        return f"{self.get_section_display()} - {self.question_text[:50]}"


class PerformanceAspect(models.Model):
    """Performance evaluation aspects"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class EvaluationForm(models.Model):
    """Individual evaluation forms"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations')
    period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE, related_name='evaluations')
    form_template = models.ForeignKey(AppraisalFormTemplate, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # JSON fields for storing evaluation data
    self_appraisal_data = models.JSONField(default=dict)
    supervisor_assessment_data = models.JSONField(default=dict)
    final_review_data = models.JSONField(default=dict)
    
    # Timestamps for each stage
    self_appraisal_submitted_at = models.DateTimeField(null=True, blank=True)
    supervisor_assessment_submitted_at = models.DateTimeField(null=True, blank=True)
    final_review_submitted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'period']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'period']),
            models.Index(fields=['status']),
            models.Index(fields=['period', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.period.name}"


class KPIResponse(models.Model):
    """Individual KPI responses for evaluation forms"""
    evaluation_form = models.ForeignKey(EvaluationForm, on_delete=models.CASCADE, related_name='kpi_responses')
    kpi = models.ForeignKey(KPITemplate, on_delete=models.CASCADE)
    self_assessment_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    self_assessment_comment = models.TextField(blank=True)
    supervisor_assessment_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supervisor_assessment_comment = models.TextField(blank=True)
    final_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_comment = models.TextField(blank=True)
    auto_calculated_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['evaluation_form', 'kpi']
        ordering = ['kpi__name']

    def __str__(self):
        return f"{self.evaluation_form.user.username} - {self.kpi.name}"


class PerformanceRating(models.Model):
    """Individual performance aspect ratings"""
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Above Average'),
        (5, 'Excellent'),
    ]
    
    evaluation_form = models.ForeignKey(EvaluationForm, on_delete=models.CASCADE, related_name='ratings')
    aspect = models.ForeignKey(PerformanceAspect, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    comments = models.TextField(blank=True)
    rated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['evaluation_form', 'aspect', 'rated_by']
        ordering = ['aspect__name']

    def __str__(self):
        return f"{self.evaluation_form.user.username} - {self.aspect.name}: {self.rating}"


class EvaluationApproval(models.Model):
    """Approval workflow tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    evaluation_form = models.ForeignKey(EvaluationForm, on_delete=models.CASCADE, related_name='approvals')
    approval_level = models.ForeignKey(ApprovalLevel, on_delete=models.CASCADE)
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluation_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['evaluation_form', 'approval_level']
        ordering = ['approval_level__level']

    def __str__(self):
        return f"{self.evaluation_form.user.username} - Level {self.approval_level.level}"


class EvaluationRecommendation(models.Model):
    """Final evaluation recommendations"""
    evaluation_form = models.ForeignKey(EvaluationForm, on_delete=models.CASCADE, related_name='recommendations')
    overall_rating = models.PositiveIntegerField(choices=PerformanceRating.RATING_CHOICES)
    strengths = models.TextField()
    areas_for_improvement = models.TextField()
    recommendations = models.TextField()
    recommended_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.evaluation_form.user.username} - {self.overall_rating}"


class TrainingNeed(models.Model):
    """Identified training needs from evaluations"""
    evaluation_form = models.ForeignKey(EvaluationForm, on_delete=models.CASCADE, related_name='training_needs')
    training_area = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ])
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    timeline = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'training_area']

    def __str__(self):
        return f"{self.evaluation_form.user.username} - {self.training_area}"


class CareerDevelopmentPlan(models.Model):
    """Career development plans from evaluations"""
    evaluation_form = models.ForeignKey(EvaluationForm, on_delete=models.CASCADE, related_name='career_plans')
    short_term_goals = models.TextField()
    long_term_goals = models.TextField()
    development_actions = models.TextField()
    timeline = models.CharField(max_length=100)
    mentor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mentored_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.evaluation_form.user.username} - Career Plan"


class AppraisalAnalytics(models.Model):
    """Analytics and insights from appraisal data"""
    period = models.ForeignKey(EvaluationPeriod, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    total_evaluations = models.PositiveIntegerField(default=0)
    completed_evaluations = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    top_performers_count = models.PositiveIntegerField(default=0)
    improvement_needed_count = models.PositiveIntegerField(default=0)
    kpi_trends = models.JSONField(default=dict)  # KPI performance trends
    approval_times = models.JSONField(default=dict)  # Average approval times
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['period', 'department']
        ordering = ['-created_at']

    def __str__(self):
        return f"Analytics - {self.period.name} - {self.department.name if self.department else 'All Departments'}"
