from django.db import transaction
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
import json

from .models import (
    EvaluationPeriod, KPITemplate, AppraisalFormTemplate, FormKPI,
    ConditionalApprovalRule, Goal, GoalProgress, PeerFeedback,
    EvaluationForm, KPIResponse, PerformanceRating, EvaluationApproval,
    EvaluationRecommendation, TrainingNeed, CareerDevelopmentPlan,
    AppraisalAnalytics
)
from core.models import Department, ApprovalWorkflow, ApprovalLevel
from users.models import UserProfile, UserRole


class KPIService:
    """Service for KPI-related operations"""
    
    @staticmethod
    def create_kpi_template(data, created_by):
        """Create a new KPI template with validation"""
        with transaction.atomic():
            kpi = KPITemplate.objects.create(
                name=data['name'],
                description=data['description'],
                kpi_type=data['kpi_type'],
                visibility=data['visibility'],
                unit_of_measure=data.get('unit_of_measure', ''),
                min_value=data.get('min_value'),
                max_value=data.get('max_value'),
                default_weight=data.get('default_weight', 1.00),
                is_auto_calculated=data.get('is_auto_calculated', False),
                data_source=data.get('data_source', ''),
                calculation_formula=data.get('calculation_formula', ''),
                created_by=created_by
            )
            
            # Add target departments
            if data.get('target_departments'):
                kpi.target_departments.set(data['target_departments'])
            
            return kpi
    
    @staticmethod
    def get_visible_kpis_for_user(user, department=None):
        """Get KPIs visible to a specific user based on their role and department"""
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        is_hr = user_roles.filter(role='hr').exists()
        is_admin = user_roles.filter(role='admin').exists()
        
        # Base queryset
        kpis = KPITemplate.objects.filter(is_active=True)
        
        # Filter by visibility
        if is_hr or is_admin:
            # HR and admin can see all KPIs
            pass
        else:
            # Regular users can only see KPIs with 'all' visibility
            # or department-specific KPIs if they're in that department
            user_department = department or user.profile.department
            kpis = kpis.filter(
                Q(visibility='all') |
                Q(visibility='department', target_departments=user_department)
            )
        
        return kpis
    
    @staticmethod
    def auto_calculate_kpi_value(kpi, user, period):
        """Auto-calculate KPI value from external data sources"""
        if not kpi.is_auto_calculated:
            return None
        
        # This is where you would integrate with external systems
        # Examples: HRIS, attendance system, sales CRM, etc.
        
        if kpi.data_source == 'attendance_system':
            return KPIService._calculate_attendance_kpi(user, period)
        elif kpi.data_source == 'sales_system':
            return KPIService._calculate_sales_kpi(user, period)
        elif kpi.data_source == 'project_management':
            return KPIService._calculate_project_kpi(user, period)
        else:
            # Custom calculation using formula
            return KPIService._calculate_custom_kpi(kpi, user, period)
    
    @staticmethod
    def _calculate_attendance_kpi(user, period):
        """Calculate attendance-based KPI"""
        # Placeholder implementation
        # In real implementation, this would query your attendance system
        return 95.5  # 95.5% attendance rate
    
    @staticmethod
    def _calculate_sales_kpi(user, period):
        """Calculate sales-based KPI"""
        # Placeholder implementation
        # In real implementation, this would query your sales CRM
        return 125000  # $125,000 in sales
    
    @staticmethod
    def _calculate_project_kpi(user, period):
        """Calculate project-based KPI"""
        # Placeholder implementation
        # In real implementation, this would query your project management system
        return 8  # 8 projects completed
    
    @staticmethod
    def _calculate_custom_kpi(kpi, user, period):
        """Calculate custom KPI using formula"""
        # This would evaluate the calculation_formula
        # For now, return a placeholder value
        return 85.0


class FormTemplateService:
    """Service for form template operations"""
    
    @staticmethod
    def create_form_template(data, created_by):
        """Create a new appraisal form template"""
        with transaction.atomic():
            template = AppraisalFormTemplate.objects.create(
                name=data['name'],
                description=data['description'],
                form_type=data['form_type'],
                approval_workflow_id=data.get('approval_workflow'),
                created_by=created_by
            )
            
            # Add target departments
            if data.get('target_departments'):
                template.target_departments.set(data['target_departments'])
            
            # Add KPIs with weights
            if data.get('kpis'):
                for i, kpi_data in enumerate(data['kpis']):
                    FormKPI.objects.create(
                        form_template=template,
                        kpi_id=kpi_data['kpi_id'],
                        weight=kpi_data.get('weight', 1.00),
                        is_required=kpi_data.get('is_required', True),
                        order=i+1
                    )
            
            return template
    
    @staticmethod
    def get_appropriate_template(user, period, form_type=None):
        """Get the most appropriate form template for a user"""
        user_department = user.profile.department
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        
        # Get available templates
        templates = AppraisalFormTemplate.objects.filter(
            is_active=True,
            target_departments=user_department
        )
        
        # Filter by form type if specified
        if form_type:
            templates = templates.filter(form_type=form_type)
        
        # Filter by staff level
        staff_level = user.profile.position.staff_level if user.profile.position else 'junior'
        templates = templates.filter(
            Q(target_staff_levels__contains=[staff_level]) |
            Q(target_staff_levels=[])
        )
        
        # Return the most specific template
        return templates.first()
    
    @staticmethod
    def clone_template(template, new_name, created_by):
        """Clone an existing form template"""
        with transaction.atomic():
            # Create new template
            new_template = AppraisalFormTemplate.objects.create(
                name=new_name,
                description=template.description,
                form_type=template.form_type,
                approval_workflow=template.approval_workflow,
                created_by=created_by
            )
            
            # Copy target departments
            new_template.target_departments.set(template.target_departments.all())
            
            # Copy KPIs
            for form_kpi in template.formkpi_set.all():
                FormKPI.objects.create(
                    form_template=new_template,
                    kpi=form_kpi.kpi,
                    weight=form_kpi.weight,
                    is_required=form_kpi.is_required,
                    order=form_kpi.order
                )
            
            return new_template


class GoalService:
    """Service for goal management"""
    
    @staticmethod
    def create_goal(data, created_by):
        """Create a new goal"""
        with transaction.atomic():
            goal = Goal.objects.create(
                title=data['title'],
                description=data['description'],
                goal_type=data['goal_type'],
                assigned_to_id=data['assigned_to'],
                created_by=created_by,
                department_id=data.get('department'),
                target_date=data['target_date'],
                kpi_target_id=data.get('kpi_target'),
                target_value=data.get('target_value'),
            )
            
            # Create initial progress record
            GoalProgress.objects.create(
                goal=goal,
                progress_percentage=0.00,
                notes="Goal created",
                updated_by=created_by
            )
            
            return goal
    
    @staticmethod
    def update_goal_progress(goal, progress_percentage, notes, updated_by):
        """Update goal progress"""
        with transaction.atomic():
            # Update goal
            goal.progress_percentage = progress_percentage
            if float(progress_percentage) >= 100:
                goal.status = 'completed'
                goal.completion_date = timezone.now().date()
            elif goal.target_date < timezone.now().date() and goal.status == 'active':
                goal.status = 'overdue'
            goal.save()
            
            # Create progress record
            GoalProgress.objects.create(
                goal=goal,
                progress_percentage=progress_percentage,
                notes=notes,
                updated_by=updated_by
            )
            
            return goal
    
    @staticmethod
    def get_goals_for_user(user, include_team=False):
        """Get goals for a user (personal and optionally team)"""
        goals = Goal.objects.filter(assigned_to=user)
        
        if include_team:
            # Add team goals if user is a supervisor
            user_roles = UserRole.objects.filter(user=user, is_active=True)
            if user_roles.filter(role='supervisor').exists():
                team_goals = Goal.objects.filter(
                    assigned_to__profile__supervisors__supervisor=user,
                    assigned_to__profile__supervisors__is_active=True
                )
                goals = goals.union(team_goals)
        
        return goals.order_by('-target_date')
    
    @staticmethod
    def auto_update_kpi_goals():
        """Automatically update goals that are linked to KPIs"""
        kpi_goals = Goal.objects.filter(
            kpi_target__isnull=False,
            status='active'
        ).select_related('kpi_target', 'assigned_to')
        
        for goal in kpi_goals:
            # Get current KPI value
            current_value = KPIService.auto_calculate_kpi_value(
                goal.kpi_target, 
                goal.assigned_to, 
                None  # You might want to pass a specific period
            )
            
            if current_value and goal.target_value:
                # Calculate progress percentage
                progress = min((current_value / goal.target_value) * 100, 100)
                GoalService.update_goal_progress(
                    goal, 
                    progress, 
                    f"Auto-updated from KPI: {goal.kpi_target.name}", 
                    goal.assigned_to
                )


class ConditionalApprovalService:
    """Service for conditional approval rules"""
    
    @staticmethod
    def check_and_apply_rules(evaluation):
        """Check and apply conditional approval rules for an evaluation"""
        rules = ConditionalApprovalRule.objects.filter(is_active=True)
        applied_rules = []
        
        for rule in rules:
            if ConditionalApprovalService._check_rule_conditions(rule, evaluation):
                result = ConditionalApprovalService._apply_rule_action(rule, evaluation)
                applied_rules.append({
                    'rule': rule,
                    'result': result
                })
        
        return applied_rules
    
    @staticmethod
    def _check_rule_conditions(rule, evaluation):
        """Check if rule conditions are met"""
        params = rule.condition_parameters
        
        if rule.condition_type == 'score_threshold':
            threshold = params.get('threshold', 50)
            avg_score = evaluation.kpi_responses.aggregate(
                avg=Avg('final_value')
            )['avg'] or 0
            return avg_score < threshold
        
        elif rule.condition_type == 'kpi_failure':
            kpi_id = params.get('kpi_id')
            min_score = params.get('min_score', 50)
            
            kpi_response = evaluation.kpi_responses.filter(kpi_id=kpi_id).first()
            if kpi_response and kpi_response.final_value:
                return kpi_response.final_value < min_score
            return False
        
        elif rule.condition_type == 'department':
            target_dept = params.get('department_id')
            return evaluation.user.profile.department_id == target_dept
        
        elif rule.condition_type == 'role':
            target_role = params.get('role')
            return UserRole.objects.filter(
                user=evaluation.user,
                role=target_role,
                is_active=True
            ).exists()
        
        return False
    
    @staticmethod
    def _apply_rule_action(rule, evaluation):
        """Apply the rule action"""
        params = rule.action_parameters
        
        if rule.action == 'add_approver':
            approver_id = params.get('approver_id')
            if approver_id:
                approval_level = ApprovalLevel.objects.get(id=params.get('approval_level_id'))
                EvaluationApproval.objects.create(
                    evaluation_form=evaluation,
                    approval_level=approval_level,
                    approver_id=approver_id,
                    status='pending'
                )
                return f"Added approver: {approval_level.name}"
        
        elif rule.action == 'escalate':
            # Move to next approval level
            current_approval = evaluation.approvals.filter(status='pending').first()
            if current_approval:
                next_level = ApprovalLevel.objects.filter(
                    level__gt=current_approval.approval_level.level
                ).order_by('level').first()
                if next_level:
                    EvaluationApproval.objects.create(
                        evaluation_form=evaluation,
                        approval_level=next_level,
                        approver_id=params.get('approver_id'),
                        status='pending'
                    )
                    return f"Escalated to level {next_level.level}"
        
        elif rule.action == 'notify_hr':
            # Send notification to HR
            return "HR notification sent"
        
        elif rule.action == 'require_improvement_plan':
            # Create improvement plan requirement
            return "Improvement plan required"
        
        return "Action applied"


class AnalyticsService:
    """Service for analytics and reporting"""
    
    @staticmethod
    def generate_period_analytics(period, department=None):
        """Generate analytics for a specific period"""
        analytics, created = AppraisalAnalytics.objects.get_or_create(
            period=period,
            department=department
        )
        
        # Calculate statistics
        evaluations = EvaluationForm.objects.filter(period=period)
        if department:
            evaluations = evaluations.filter(user__profile__department=department)
        
        analytics.total_evaluations = evaluations.count()
        analytics.completed_evaluations = evaluations.filter(status='approved').count()
        
        # Calculate average score
        avg_score = evaluations.aggregate(
            avg=Avg('kpi_responses__final_value')
        )['avg']
        analytics.average_score = avg_score if avg_score else 0
        
        # Count top performers (score > 80)
        top_performers = evaluations.filter(
            kpi_responses__final_value__gt=80
        ).distinct().count()
        analytics.top_performers_count = top_performers
        
        # Count improvement needed (score < 50)
        improvement_needed = evaluations.filter(
            kpi_responses__final_value__lt=50
        ).distinct().count()
        analytics.improvement_needed_count = improvement_needed
        
        # KPI trends
        kpi_trends = {}
        kpis = KPITemplate.objects.filter(is_active=True)
        for kpi in kpis:
            avg_kpi_score = evaluations.filter(
                kpi_responses__kpi=kpi
            ).aggregate(avg=Avg('kpi_responses__final_value'))['avg']
            if avg_kpi_score:
                kpi_trends[kpi.name] = float(avg_kpi_score)
        analytics.kpi_trends = kpi_trends
        
        # Approval times
        approval_times = {}
        approvals = EvaluationApproval.objects.filter(
            evaluation_form__period=period,
            status='approved'
        )
        if department:
            approvals = approvals.filter(evaluation_form__user__profile__department=department)
        
        for approval in approvals:
            if approval.approved_at and approval.created_at:
                time_diff = (approval.approved_at - approval.created_at).total_seconds() / 3600  # hours
                level_name = approval.approval_level.name
                if level_name not in approval_times:
                    approval_times[level_name] = []
                approval_times[level_name].append(time_diff)
        
        # Calculate average approval times
        avg_approval_times = {}
        for level, times in approval_times.items():
            avg_approval_times[level] = sum(times) / len(times)
        analytics.approval_times = avg_approval_times
        
        analytics.save()
        return analytics
    
    @staticmethod
    def get_department_performance_comparison(period):
        """Compare performance across departments"""
        departments = Department.objects.filter(is_active=True)
        comparison_data = []
        
        for dept in departments:
            analytics = AnalyticsService.generate_period_analytics(period, dept)
            comparison_data.append({
                'department': dept.name,
                'total_evaluations': analytics.total_evaluations,
                'completion_rate': (analytics.completed_evaluations / analytics.total_evaluations * 100) if analytics.total_evaluations > 0 else 0,
                'average_score': analytics.average_score,
                'top_performers_rate': (analytics.top_performers_count / analytics.total_evaluations * 100) if analytics.total_evaluations > 0 else 0,
            })
        
        return comparison_data
    
    @staticmethod
    def get_kpi_performance_trends(period, kpi_ids=None):
        """Get KPI performance trends"""
        kpis = KPITemplate.objects.filter(is_active=True)
        if kpi_ids:
            kpis = kpis.filter(id__in=kpi_ids)
        
        trends = []
        for kpi in kpis:
            avg_score = KPIResponse.objects.filter(
                evaluation_form__period=period,
                kpi=kpi,
                final_value__isnull=False
            ).aggregate(avg=Avg('final_value'))['avg']
            
            if avg_score:
                trends.append({
                    'kpi_name': kpi.name,
                    'average_score': float(avg_score),
                    'unit': kpi.unit_of_measure,
                    'total_responses': KPIResponse.objects.filter(
                        evaluation_form__period=period,
                        kpi=kpi
                    ).count()
                })
        
        return sorted(trends, key=lambda x: x['average_score'], reverse=True)


class NotificationService:
    """Service for sending notifications"""
    
    @staticmethod
    def send_evaluation_notification(evaluation, notification_type):
        """Send notification for evaluation events"""
        # This would integrate with your notification system
        # For now, we'll just log the notification
        
        notification_data = {
            'evaluation_id': evaluation.id,
            'user_id': evaluation.user.id,
            'notification_type': notification_type,
            'timestamp': timezone.now().isoformat(),
        }
        
        # In a real implementation, you would:
        # 1. Send email notification
        # 2. Send in-app notification
        # 3. Send Slack/Teams notification if configured
        
        print(f"Notification sent: {notification_data}")
        return notification_data
    
    @staticmethod
    def send_approval_reminder(approval):
        """Send reminder for pending approvals"""
        return NotificationService.send_evaluation_notification(
            approval.evaluation_form,
            'approval_reminder'
        )
    
    @staticmethod
    def send_goal_deadline_reminder(goal):
        """Send reminder for goal deadlines"""
        notification_data = {
            'goal_id': goal.id,
            'user_id': goal.assigned_to.id,
            'notification_type': 'goal_deadline_reminder',
            'timestamp': timezone.now().isoformat(),
        }
        
        print(f"Goal deadline reminder: {notification_data}")
        return notification_data 