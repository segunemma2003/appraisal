from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from core.models import Department
from users.models import UserProfile


class EvaluationPeriod(models.Model):
    """Evaluation periods and timeframes"""
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    submission_deadline = models.DateTimeField(default=timezone.now)
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
    """Dynamic KPI templates with role-based creation permissions"""
    KPI_TYPE_CHOICES = [
        ('quantitative', 'Quantitative'),
        ('qualitative', 'Qualitative'),
        ('percentage', 'Percentage'),
        ('currency', 'Currency'),
        ('boolean', 'Yes/No'),
        ('rating', 'Rating'),
        ('count', 'Count'),
        ('duration', 'Duration'),
        ('ratio', 'Ratio'),
        ('index', 'Index'),
    ]
    
    VISIBILITY_CHOICES = [
        ('all', 'All Staff'),
        ('management', 'Management Only'),
        ('hr', 'HR Only'),
        ('department', 'Department Specific'),
        ('role', 'Role Specific'),
        ('level', 'Level Specific'),
        ('custom', 'Custom Targeting'),
    ]
    
    # Basic KPI information
    name = models.CharField(max_length=200)
    description = models.TextField()
    kpi_type = models.CharField(max_length=20, choices=KPI_TYPE_CHOICES)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='all')
    
    # Role-based targeting
    target_roles = models.ManyToManyField('core.Role', blank=True, related_name='kpi_templates')
    target_staff_levels = models.JSONField(default=list, blank=True)
    target_departments = models.ManyToManyField('core.Department', blank=True, related_name='kpi_templates')
    target_positions = models.ManyToManyField('core.Position', blank=True, related_name='kpi_templates')
    
    # KPI configuration
    unit_of_measure = models.CharField(max_length=50, blank=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    default_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    target_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Auto-calculation settings
    is_auto_calculated = models.BooleanField(default=False)
    data_source = models.CharField(max_length=100, blank=True)
    calculation_formula = models.TextField(blank=True)
    calculation_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('on_demand', 'On Demand'),
    ], default='monthly')
    
    # Creation permissions
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_by_role = models.ForeignKey('core.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_kpis')
    creation_permissions = models.JSONField(default=dict, blank=True)  # Who can create this KPI
    
    # KPI behavior
    is_active = models.BooleanField(default=True)
    is_template = models.BooleanField(default=False)
    template_category = models.CharField(max_length=50, blank=True)
    requires_approval = models.BooleanField(default=False)
    approval_workflow = models.ForeignKey('core.ApprovalWorkflow', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Scoring and evaluation
    scoring_method = models.CharField(max_length=20, choices=[
        ('linear', 'Linear'),
        ('exponential', 'Exponential'),
        ('threshold', 'Threshold'),
        ('custom', 'Custom Formula'),
    ], default='linear')
    scoring_criteria = models.JSONField(default=dict, blank=True)
    
    # Metadata
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'version']

    def __str__(self):
        return f"{self.name} (v{self.version})"

    @property
    def is_role_specific(self):
        """Check if this KPI is targeted to specific roles"""
        return self.visibility == 'role' and self.target_roles.exists()

    @property
    def is_level_specific(self):
        """Check if this KPI is targeted to specific staff levels"""
        return self.visibility == 'level' and bool(self.target_staff_levels)

    def is_visible_for_user(self, user):
        """Check if this KPI should be visible for a specific user"""
        user_roles = user.core_user_roles.filter(is_active=True)
        user_department = getattr(user.profile, 'department', None)
        user_position = getattr(user.profile, 'position', None)
        
        # Check visibility settings
        if self.visibility == 'all':
            return True
        elif self.visibility == 'management':
            return any(ur.role.role_level in ['manager', 'director', 'executive'] for ur in user_roles)
        elif self.visibility == 'hr':
            return any(ur.role.codename == 'hr' for ur in user_roles)
        elif self.visibility == 'department':
            return user_department and user_department in self.target_departments.all()
        elif self.visibility == 'role':
            return any(ur.role in self.target_roles.all() for ur in user_roles)
        elif self.visibility == 'level':
            if user_position:
                return user_position.staff_level in self.target_staff_levels
            return False
        elif self.visibility == 'custom':
            # Check all targeting criteria
            if self.target_roles.exists():
                if not any(ur.role in self.target_roles.all() for ur in user_roles):
                    return False
            if self.target_staff_levels and user_position:
                if user_position.staff_level not in self.target_staff_levels:
                    return False
            if self.target_departments.exists():
                if not user_department or user_department not in self.target_departments.all():
                    return False
            if self.target_positions.exists():
                if not user_position or user_position not in self.target_positions.all():
                    return False
            return True
        
        return False

    def can_be_created_by_user(self, user):
        """Check if a user can create this type of KPI"""
        user_roles = user.core_user_roles.filter(is_active=True)
        
        # Check creation permissions
        for user_role in user_roles:
            if user_role.role.can_create_kpis:
                # Check if user's role can create KPIs for target roles
                if self.target_roles.exists():
                    for target_role in self.target_roles.all():
                        if user_role.role.can_create_kpi_for_role(target_role):
                            return True
                else:
                    # No specific target roles, check general permission
                    return True
        
        return False

    def calculate_score(self, actual_value):
        """Calculate score based on actual value and scoring criteria"""
        if not actual_value or not self.is_active:
            return 0
        
        try:
            actual = float(actual_value)
            target = float(self.target_value) if self.target_value else 0
            threshold = float(self.threshold_value) if self.threshold_value else 0
            
            if self.scoring_method == 'linear':
                if target > 0:
                    return min((actual / target) * 100, 100)
                return 0
            
            elif self.scoring_method == 'threshold':
                if actual >= threshold:
                    return 100
                elif actual > 0:
                    return (actual / threshold) * 100
                return 0
            
            elif self.scoring_method == 'exponential':
                if target > 0:
                    ratio = actual / target
                    return min((ratio ** 2) * 100, 100)
                return 0
            
            elif self.scoring_method == 'custom':
                # Use custom formula from scoring_criteria
                formula = self.scoring_criteria.get('formula', '')
                if formula:
                    # This would need a safe formula evaluator
                    return self._evaluate_custom_formula(formula, actual, target, threshold)
                return 0
            
            return 0
            
        except (ValueError, TypeError):
            return 0

    def _evaluate_custom_formula(self, formula, actual, target, threshold):
        """Evaluate custom scoring formula (simplified implementation)"""
        try:
            # This is a simplified implementation
            # In production, you'd want a proper formula parser
            if 'actual' in formula and 'target' in formula:
                # Replace variables with values
                eval_formula = formula.replace('actual', str(actual)).replace('target', str(target))
                return min(eval(eval_formula), 100)
            return 0
        except:
            return 0

    def clone_kpi(self, new_name=None, new_version=None):
        """Clone this KPI for reuse"""
        new_kpi = KPITemplate.objects.create(
            name=new_name or f"{self.name} (Copy)",
            description=self.description,
            kpi_type=self.kpi_type,
            visibility=self.visibility,
            unit_of_measure=self.unit_of_measure,
            min_value=self.min_value,
            max_value=self.max_value,
            default_weight=self.default_weight,
            target_value=self.target_value,
            threshold_value=self.threshold_value,
            is_auto_calculated=self.is_auto_calculated,
            data_source=self.data_source,
            calculation_formula=self.calculation_formula,
            calculation_frequency=self.calculation_frequency,
            scoring_method=self.scoring_method,
            scoring_criteria=self.scoring_criteria,
            is_template=True,
            template_category=self.template_category,
            version=new_version or 1
        )
        
        # Copy targeting
        new_kpi.target_roles.set(self.target_roles.all())
        new_kpi.target_staff_levels = self.target_staff_levels
        new_kpi.target_departments.set(self.target_departments.all())
        new_kpi.target_positions.set(self.target_positions.all())
        
        return new_kpi


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
    approval_workflow = models.ForeignKey('core.ApprovalWorkflow', on_delete=models.SET_NULL, null=True, blank=True)
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
    """Dynamic evaluation questions with role-based targeting"""
    STAFF_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('junior', 'Junior Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('lead', 'Lead Level'),
        ('manager', 'Manager Level'),
        ('director', 'Director Level'),
        ('executive', 'Executive Level'),
    ]
    
    SECTION_CHOICES = [
        ('personal_data', 'Personal Data'),
        ('qualifications', 'Qualifications'),
        ('training', 'Training'),
        ('responsibilities', 'Responsibilities'),
        ('challenges', 'Challenges'),
        ('goals', 'Goals'),
        ('leadership', 'Leadership'),
        ('teamwork', 'Teamwork'),
        ('innovation', 'Innovation'),
        ('communication', 'Communication'),
        ('problem_solving', 'Problem Solving'),
        ('technical_skills', 'Technical Skills'),
        ('project_management', 'Project Management'),
        ('customer_service', 'Customer Service'),
        ('quality_management', 'Quality Management'),
        ('compliance', 'Compliance'),
        ('safety', 'Safety'),
        ('performance', 'Performance'),
        ('development', 'Development'),
        ('feedback', 'Feedback'),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('textarea', 'Text Area'),
        ('select', 'Select'),
        ('date', 'Date'),
        ('number', 'Number'),
        ('rating', 'Rating'),
        ('boolean', 'Yes/No'),
        ('file_upload', 'File Upload'),
        ('signature', 'Digital Signature'),
        ('matrix', 'Matrix Question'),
        ('ranking', 'Ranking'),
        ('scale', 'Scale'),
    ]
    
    # Basic question information
    question_text = models.CharField(max_length=500, default="")
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default="personal_data")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default="text")
    
    # Role-based targeting
    target_roles = models.ManyToManyField('core.Role', blank=True, related_name='evaluation_questions')
    target_staff_levels = models.JSONField(default=list, blank=True)  # List of staff levels
    target_departments = models.ManyToManyField('core.Department', blank=True, related_name='evaluation_questions')
    
    # Question configuration
    options = models.TextField(blank=True)  # For select, rating, scale questions
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    default_value = models.TextField(blank=True)
    placeholder_text = models.CharField(max_length=200, blank=True)
    help_text = models.TextField(blank=True)
    
    # Question behavior
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    is_required = models.BooleanField(default=True)
    scoring_criteria = models.JSONField(default=dict, blank=True)
    
    # Conditional logic
    depends_on_question = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_questions')
    condition_type = models.CharField(max_length=20, choices=[
        ('equals', 'Equals'),
        ('not_equals', 'Not Equals'),
        ('contains', 'Contains'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('is_empty', 'Is Empty'),
        ('is_not_empty', 'Is Not Empty'),
    ], blank=True)
    condition_value = models.TextField(blank=True)
    
    # Question metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_template = models.BooleanField(default=False)
    template_category = models.CharField(max_length=50, blank=True)
    version = models.PositiveIntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section', 'order']
        unique_together = ['section', 'order', 'version']

    def __str__(self):
        return f"{self.get_section_display()} - {self.question_text[:50]}"

    @property
    def is_conditional(self):
        """Check if this question has conditional logic"""
        return bool(self.depends_on_question and self.condition_type)

    def is_visible_for_user(self, user):
        """Check if this question should be visible for a specific user"""
        user_roles = user.core_user_roles.filter(is_active=True)
        user_department = getattr(user.profile, 'department', None)
        
        # Check role targeting
        if self.target_roles.exists():
            if not any(ur.role in self.target_roles.all() for ur in user_roles):
                return False
        
        # Check staff level targeting
        if self.target_staff_levels:
            user_staff_level = getattr(user.profile.position, 'staff_level', 'junior')
            if user_staff_level not in self.target_staff_levels:
                return False
        
        # Check department targeting
        if self.target_departments.exists():
            if not user_department or user_department not in self.target_departments.all():
                return False
        
        return True

    def get_options_list(self):
        """Get options as a list for select/rating questions"""
        if not self.options:
            return []
        return [option.strip() for option in self.options.split('\n') if option.strip()]

    def get_scoring_criteria(self):
        """Get scoring criteria for the question"""
        return self.scoring_criteria or {}

    def calculate_score(self, answer_value):
        """Calculate score based on answer and scoring criteria"""
        if not self.is_required or not answer_value:
            return 0
        
        criteria = self.get_scoring_criteria()
        
        if self.question_type == 'rating':
            try:
                rating = float(answer_value)
                max_rating = criteria.get('max_rating', 5)
                return (rating / max_rating) * self.weight
            except (ValueError, TypeError):
                return 0
        
        elif self.question_type == 'select':
            option_scores = criteria.get('option_scores', {})
            return option_scores.get(str(answer_value), 0) * self.weight
        
        elif self.question_type == 'number':
            try:
                value = float(answer_value)
                min_val = criteria.get('min_value', self.min_value)
                max_val = criteria.get('max_value', self.max_value)
                
                if min_val and max_val:
                    normalized = (value - min_val) / (max_val - min_val)
                    return normalized * self.weight
                return value * self.weight
            except (ValueError, TypeError):
                return 0
        
        return 0

    def clone_question(self, new_section=None, new_order=None):
        """Clone this question for reuse"""
        new_question = EvaluationQuestion.objects.create(
            question_text=self.question_text,
            section=new_section or self.section,
            question_type=self.question_type,
            options=self.options,
            min_value=self.min_value,
            max_value=self.max_value,
            default_value=self.default_value,
            placeholder_text=self.placeholder_text,
            help_text=self.help_text,
            required=self.required,
            order=new_order or self.order,
            weight=self.weight,
            is_required=self.is_required,
            scoring_criteria=self.scoring_criteria,
            is_template=True,
            template_category=self.template_category,
            version=1
        )
        
        # Copy targeting
        new_question.target_roles.set(self.target_roles.all())
        new_question.target_staff_levels = self.target_staff_levels
        new_question.target_departments.set(self.target_departments.all())
        
        return new_question


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
    approval_level = models.ForeignKey('core.ApprovalLevel', on_delete=models.CASCADE)
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
    overall_rating = models.PositiveIntegerField(choices=PerformanceRating.RATING_CHOICES, default=3)
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
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
    training_area = models.CharField(max_length=200, default="")
    description = models.TextField(blank=True)
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
    short_term_goals = models.TextField(blank=True)
    long_term_goals = models.TextField(blank=True)
    job_description = models.TextField(blank=True)
    development_actions = models.TextField(blank=True)
    timeline = models.CharField(max_length=100, blank=True)
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
