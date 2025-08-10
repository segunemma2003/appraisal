from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('export-analytics/', views.export_analytics, name='export_analytics'),
    
    # KPI Management
    path('kpi-library/', views.kpi_library, name='kpi_library'),
    path('kpi/create/', views.create_kpi, name='create_kpi'),
    path('kpi/<int:kpi_id>/edit/', views.edit_kpi, name='edit_kpi'),
    
    # Form Template Management
    path('form-templates/', views.form_templates, name='form_templates'),
    path('form-templates/create/', views.create_form_template, name='create_form_template'),
    
    # Goal Management
    path('goals/', views.goal_management, name='goal_management'),
    path('goals/create/', views.create_goal, name='create_goal'),
    path('goals/<int:goal_id>/progress/', views.update_goal_progress, name='update_goal_progress'),
    
    # Peer Feedback
    path('peer-feedback/<int:evaluation_id>/', views.peer_feedback, name='peer_feedback'),
    
    # API Endpoints
    path('api/auto-calculate-kpi/', views.auto_calculate_kpi, name='auto_calculate_kpi'),
    path('api/apply-conditional-approval/', views.apply_conditional_approval, name='apply_conditional_approval'),
] 