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

from .models import (
    EvaluationPeriod, KPITemplate, AppraisalFormTemplate, FormKPI,
    ConditionalApprovalRule, Goal, GoalProgress, PeerFeedback,
    EvaluationForm, KPIResponse, PerformanceRating, EvaluationApproval,
    EvaluationRecommendation, TrainingNeed, CareerDevelopmentPlan,
    AppraisalAnalytics, EvaluationQuestion
)
from .services import (
    KPIService, FormTemplateService, GoalService, 
    ConditionalApprovalService, AnalyticsService, NotificationService
)
from core.models import Department, Role, UserRole
from core.permissions import has_permission, get_user_permissions
from users.models import UserProfile


# ============================================================================
# DYNAMIC QUESTIONS MANAGEMENT APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def evaluation_question_list(request):
    """List and create evaluation questions"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        questions = EvaluationQuestion.objects.filter(is_active=True)
        
        # Filter by section
        section = request.GET.get('section')
        if section:
            questions = questions.filter(section=section)
        
        # Filter by staff level
        staff_level = request.GET.get('staff_level')
        if staff_level:
            questions = questions.filter(staff_level=staff_level)
        
        # Filter by question type
        question_type = request.GET.get('question_type')
        if question_type:
            questions = questions.filter(question_type=question_type)
        
        data = {
            'questions': [{
                'id': q.id,
                'question_text': q.question_text,
                'section': q.section,
                'section_display': q.get_section_display(),
                'staff_level': q.staff_level,
                'staff_level_display': q.get_staff_level_display(),
                'question_type': q.question_type,
                'question_type_display': q.get_question_type_display(),
                'options': q.options,
                'required': q.required,
                'order': q.order,
                'created_at': q.created_at,
            } for q in questions]
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'create', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                data = request.data
                
                question = EvaluationQuestion.objects.create(
                    question_text=data['question_text'],
                    section=data['section'],
                    staff_level=data['staff_level'],
                    question_type=data['question_type'],
                    options=data.get('options', ''),
                    required=data.get('required', True),
                    order=data.get('order', 1),
                )
                
                return Response({
                    'id': question.id,
                    'question_text': question.question_text,
                    'message': 'Question created successfully'
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def evaluation_question_detail(request, question_id):
    """Get, update, or delete a specific evaluation question"""
    question = get_object_or_404(EvaluationQuestion, id=question_id)
    
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        data = {
            'id': question.id,
            'question_text': question.question_text,
            'section': question.section,
            'section_display': question.get_section_display(),
            'staff_level': question.staff_level,
            'staff_level_display': question.get_staff_level_display(),
            'question_type': question.question_type,
            'question_type_display': question.get_question_type_display(),
            'options': question.options,
            'required': question.required,
            'order': question.order,
            'created_at': question.created_at,
            'updated_at': question.updated_at,
        }
        
        return Response(data)
    
    elif request.method == 'PUT':
        if not has_permission(request.user, 'update', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            data = request.data
            
            if 'question_text' in data:
                question.question_text = data['question_text']
            if 'section' in data:
                question.section = data['section']
            if 'staff_level' in data:
                question.staff_level = data['staff_level']
            if 'question_type' in data:
                question.question_type = data['question_type']
            if 'options' in data:
                question.options = data['options']
            if 'required' in data:
                question.required = data['required']
            if 'order' in data:
                question.order = data['order']
            
            question.save()
            
            return Response({'message': 'Question updated successfully'})
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not has_permission(request.user, 'delete', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        question.is_active = False
        question.save()
        
        return Response({'message': 'Question deleted successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def evaluation_question_choices(request):
    """Get available question choices"""
    data = {
        'sections': EvaluationQuestion.SECTION_CHOICES,
        'staff_levels': EvaluationQuestion.STAFF_LEVEL_CHOICES,
        'question_types': EvaluationQuestion.QUESTION_TYPE_CHOICES,
    }
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_questions_for_user(request, user_id):
    """Get evaluation questions appropriate for a specific user"""
    if not has_permission(request.user, 'read', 'form_template'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        
        # Get user's staff level
        staff_level = 'junior'  # default
        if profile.position:
            staff_level = profile.position.staff_level
        
        # Get questions for this staff level
        questions = EvaluationQuestion.objects.filter(
            is_active=True,
            staff_level=staff_level
        ).order_by('section', 'order')
        
        # Group questions by section
        questions_by_section = {}
        for question in questions:
            section = question.get_section_display()
            if section not in questions_by_section:
                questions_by_section[section] = []
            
            questions_by_section[section].append({
                'id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'question_type_display': question.get_question_type_display(),
                'options': question.options,
                'required': question.required,
                'order': question.order,
            })
        
        data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'staff_level': staff_level,
                'department': profile.department.name if profile.department else None,
            },
            'questions_by_section': questions_by_section,
        }
        
        return Response(data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# FORM TEMPLATE MANAGEMENT APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def form_template_list(request):
    """List and create form templates"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        templates = AppraisalFormTemplate.objects.filter(is_active=True)
        
        # Filter by form type
        form_type = request.GET.get('form_type')
        if form_type:
            templates = templates.filter(form_type=form_type)
        
        # Filter by department
        department_id = request.GET.get('department_id')
        if department_id:
            templates = templates.filter(target_departments__id=department_id)
        
        data = {
            'templates': [{
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'form_type': template.form_type,
                'form_type_display': template.get_form_type_display(),
                'target_departments': [dept.name for dept in template.target_departments.all()],
                'target_staff_levels': template.target_staff_levels,
                'kpis_count': template.kpis.count(),
                'approval_workflow': template.approval_workflow.name if template.approval_workflow else None,
                'created_by': template.created_by.username if template.created_by else None,
                'version': template.version,
                'created_at': template.created_at,
            } for template in templates]
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'create', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            data = request.data
            template = FormTemplateService.create_form_template(data, request.user)
            
            return Response({
                'id': template.id,
                'name': template.name,
                'message': 'Form template created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def form_template_detail(request, template_id):
    """Get, update, or delete a specific form template"""
    template = get_object_or_404(AppraisalFormTemplate, id=template_id)
    
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        kpis = template.formkpi_set.all().select_related('kpi')
        
        data = {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'form_type': template.form_type,
            'form_type_display': template.get_form_type_display(),
            'target_departments': [{
                'id': dept.id,
                'name': dept.name
            } for dept in template.target_departments.all()],
            'target_staff_levels': template.target_staff_levels,
            'kpis': [{
                'id': fk.kpi.id,
                'name': fk.kpi.name,
                'weight': fk.weight,
                'is_required': fk.is_required,
                'order': fk.order,
            } for fk in kpis],
            'approval_workflow': {
                'id': template.approval_workflow.id,
                'name': template.approval_workflow.name
            } if template.approval_workflow else None,
            'created_by': template.created_by.username if template.created_by else None,
            'version': template.version,
            'created_at': template.created_at,
            'updated_at': template.updated_at,
        }
        
        return Response(data)
    
    elif request.method == 'PUT':
        if not has_permission(request.user, 'update', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                data = request.data
                
                # Update template fields
                if 'name' in data:
                    template.name = data['name']
                if 'description' in data:
                    template.description = data['description']
                if 'form_type' in data:
                    template.form_type = data['form_type']
                if 'approval_workflow' in data:
                    template.approval_workflow_id = data['approval_workflow']
                
                template.save()
                
                # Update target departments
                if 'target_departments' in data:
                    template.target_departments.set(data['target_departments'])
                
                # Update target staff levels
                if 'target_staff_levels' in data:
                    template.target_staff_levels = data['target_staff_levels']
                    template.save()
                
                # Update KPIs
                if 'kpis' in data:
                    # Remove existing KPIs
                    template.formkpi_set.all().delete()
                    
                    # Add new KPIs
                    for i, kpi_data in enumerate(data['kpis']):
                        FormKPI.objects.create(
                            form_template=template,
                            kpi_id=kpi_data['kpi_id'],
                            weight=kpi_data.get('weight', 1.00),
                            is_required=kpi_data.get('is_required', True),
                            order=i+1
                        )
                
                return Response({'message': 'Form template updated successfully'})
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not has_permission(request.user, 'delete', 'form_template'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        template.is_active = False
        template.save()
        
        return Response({'message': 'Form template deleted successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clone_form_template(request, template_id):
    """Clone an existing form template"""
    if not has_permission(request.user, 'create', 'form_template'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        template = get_object_or_404(AppraisalFormTemplate, id=template_id)
        data = request.data
        
        new_name = data.get('name', f"{template.name} (Copy)")
        new_template = FormTemplateService.clone_template(template, new_name, request.user)
        
        return Response({
            'id': new_template.id,
            'name': new_template.name,
            'message': 'Form template cloned successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_appropriate_template(request, user_id, form_type=None):
    """Get the most appropriate form template for a user"""
    if not has_permission(request.user, 'read', 'form_template'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = get_object_or_404(User, id=user_id)
        template = FormTemplateService.get_appropriate_template(user, None, form_type)
        
        if template:
            data = {
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'form_type': template.form_type,
                'form_type_display': template.get_form_type_display(),
            }
        else:
            data = None
        
        return Response({'template': data})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# KPI MANAGEMENT APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def kpi_template_list(request):
    """List and create KPI templates"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'kpi'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        kpis = KPIService.get_visible_kpis_for_user(request.user)
        
        # Filter by KPI type
        kpi_type = request.GET.get('kpi_type')
        if kpi_type:
            kpis = kpis.filter(kpi_type=kpi_type)
        
        # Filter by visibility
        visibility = request.GET.get('visibility')
        if visibility:
            kpis = kpis.filter(visibility=visibility)
        
        data = {
            'kpis': [{
                'id': kpi.id,
                'name': kpi.name,
                'description': kpi.description,
                'kpi_type': kpi.kpi_type,
                'kpi_type_display': kpi.get_kpi_type_display(),
                'visibility': kpi.visibility,
                'visibility_display': kpi.get_visibility_display(),
                'unit_of_measure': kpi.unit_of_measure,
                'min_value': kpi.min_value,
                'max_value': kpi.max_value,
                'default_weight': kpi.default_weight,
                'is_auto_calculated': kpi.is_auto_calculated,
                'data_source': kpi.data_source,
                'target_departments': [dept.name for dept in kpi.target_departments.all()],
                'created_by': kpi.created_by.username if kpi.created_by else None,
                'version': kpi.version,
                'created_at': kpi.created_at,
            } for kpi in kpis]
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'create', 'kpi'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            data = request.data
            kpi = KPIService.create_kpi_template(data, request.user)
            
            return Response({
                'id': kpi.id,
                'name': kpi.name,
                'message': 'KPI template created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kpi_choices(request):
    """Get available KPI choices"""
    data = {
        'kpi_types': KPITemplate.KPI_TYPE_CHOICES,
        'visibility_choices': KPITemplate.VISIBILITY_CHOICES,
    }
    return Response(data)


# ============================================================================
# EVALUATION PERIOD MANAGEMENT APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def evaluation_period_list(request):
    """List and create evaluation periods"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'evaluation'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        periods = EvaluationPeriod.objects.filter(is_active=True).order_by('-start_date')
        
        data = {
            'periods': [{
                'id': period.id,
                'name': period.name,
                'start_date': period.start_date,
                'end_date': period.end_date,
                'submission_deadline': period.submission_deadline,
                'is_active': period.is_active,
                'is_open_for_submission': period.is_open_for_submission,
                'description': period.description,
                'evaluations_count': period.evaluations.count(),
                'created_at': period.created_at,
            } for period in periods]
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'create', 'evaluation'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            data = request.data
            
            period = EvaluationPeriod.objects.create(
                name=data['name'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                submission_deadline=data['submission_deadline'],
                is_open_for_submission=data.get('is_open_for_submission', False),
                description=data.get('description', ''),
            )
            
            return Response({
                'id': period.id,
                'name': period.name,
                'message': 'Evaluation period created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# CONDITIONAL APPROVAL RULES APIs
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conditional_approval_rule_list(request):
    """List and create conditional approval rules"""
    if request.method == 'GET':
        if not has_permission(request.user, 'read', 'approval'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        rules = ConditionalApprovalRule.objects.filter(is_active=True)
        
        data = {
            'rules': [{
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'condition_type': rule.condition_type,
                'condition_type_display': rule.get_condition_type_display(),
                'condition_parameters': rule.condition_parameters,
                'action': rule.action,
                'action_display': rule.get_action_display(),
                'action_parameters': rule.action_parameters,
                'created_at': rule.created_at,
            } for rule in rules]
        }
        
        return Response(data)
    
    elif request.method == 'POST':
        if not has_permission(request.user, 'create', 'approval'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            data = request.data
            
            rule = ConditionalApprovalRule.objects.create(
                name=data['name'],
                description=data['description'],
                condition_type=data['condition_type'],
                condition_parameters=data['condition_parameters'],
                action=data['action'],
                action_parameters=data['action_parameters'],
            )
            
            return Response({
                'id': rule.id,
                'name': rule.name,
                'message': 'Conditional approval rule created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conditional_approval_choices(request):
    """Get available conditional approval choices"""
    data = {
        'condition_types': ConditionalApprovalRule.CONDITION_TYPE_CHOICES,
        'actions': ConditionalApprovalRule.ACTION_CHOICES,
    }
    return Response(data)


# ============================================================================
# ANALYTICS APIs
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_period(request, period_id):
    """Get analytics for a specific period"""
    if not has_permission(request.user, 'view_analytics', 'analytics'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        period = get_object_or_404(EvaluationPeriod, id=period_id)
        department_id = request.GET.get('department_id')
        
        department = None
        if department_id:
            department = get_object_or_404(Department, id=department_id)
        
        analytics = AnalyticsService.generate_period_analytics(period, department)
        
        data = {
            'period': {
                'id': period.id,
                'name': period.name,
                'start_date': period.start_date,
                'end_date': period.end_date,
            },
            'department': {
                'id': department.id,
                'name': department.name
            } if department else None,
            'total_evaluations': analytics.total_evaluations,
            'completed_evaluations': analytics.completed_evaluations,
            'completion_rate': (analytics.completed_evaluations / analytics.total_evaluations * 100) if analytics.total_evaluations > 0 else 0,
            'average_score': analytics.average_score,
            'top_performers_count': analytics.top_performers_count,
            'improvement_needed_count': analytics.improvement_needed_count,
            'kpi_trends': analytics.kpi_trends,
            'approval_times': analytics.approval_times,
        }
        
        return Response(data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_department_comparison(request, period_id):
    """Compare performance across departments"""
    if not has_permission(request.user, 'view_analytics', 'analytics'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        period = get_object_or_404(EvaluationPeriod, id=period_id)
        comparison_data = AnalyticsService.get_department_performance_comparison(period)
        
        return Response({'comparison': comparison_data})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_kpi_trends(request, period_id):
    """Get KPI performance trends"""
    if not has_permission(request.user, 'view_analytics', 'analytics'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        period = get_object_or_404(EvaluationPeriod, id=period_id)
        kpi_ids = request.GET.getlist('kpi_ids')
        
        trends = AnalyticsService.get_kpi_performance_trends(period, kpi_ids if kpi_ids else None)
        
        return Response({'trends': trends})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
