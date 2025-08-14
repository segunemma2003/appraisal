from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    # ============================================================================
    # DYNAMIC QUESTIONS MANAGEMENT URLs
    # ============================================================================
    path('questions/', views.evaluation_question_list, name='evaluation_question_list'),
    path('questions/<int:question_id>/', views.evaluation_question_detail, name='evaluation_question_detail'),
    path('questions/choices/', views.evaluation_question_choices, name='evaluation_question_choices'),
    path('questions/user/<int:user_id>/', views.get_questions_for_user, name='get_questions_for_user'),
    
    # ============================================================================
    # FORM TEMPLATE MANAGEMENT URLs
    # ============================================================================
    path('form-templates/', views.form_template_list, name='form_template_list'),
    path('form-templates/<int:template_id>/', views.form_template_detail, name='form_template_detail'),
    path('form-templates/<int:template_id>/clone/', views.clone_form_template, name='clone_form_template'),
    path('form-templates/user/<int:user_id>/', views.get_appropriate_template, name='get_appropriate_template'),
    
    # ============================================================================
    # KPI MANAGEMENT URLs
    # ============================================================================
    path('kpis/', views.kpi_template_list, name='kpi_template_list'),
    path('kpis/choices/', views.kpi_choices, name='kpi_choices'),
    
    # ============================================================================
    # EVALUATION PERIOD MANAGEMENT URLs
    # ============================================================================
    path('periods/', views.evaluation_period_list, name='evaluation_period_list'),
    
    # ============================================================================
    # CONDITIONAL APPROVAL RULES URLs
    # ============================================================================
    path('approval-rules/', views.conditional_approval_rule_list, name='conditional_approval_rule_list'),
    path('approval-rules/choices/', views.conditional_approval_choices, name='conditional_approval_choices'),
    
    # ============================================================================
    # ANALYTICS URLs
    # ============================================================================
    path('analytics/period/<int:period_id>/', views.analytics_period, name='analytics_period'),
    path('analytics/period/<int:period_id>/department-comparison/', views.analytics_department_comparison, name='analytics_department_comparison'),
    path('analytics/period/<int:period_id>/kpi-trends/', views.analytics_kpi_trends, name='analytics_kpi_trends'),
] 