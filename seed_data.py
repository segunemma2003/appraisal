#!/usr/bin/env python
"""
Seed data script for the Dynamic Role-Based Appraisal System
This script populates the database with default roles, permissions, questions, and KPIs
"""

import os
import sys
import django
from django.utils import timezone
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import (
    Department, Position, Permission, Role, RolePermission, 
    UserRole, SystemConfiguration
)
from evaluations.models import (
    EvaluationQuestion, KPITemplate, AppraisalFormTemplate,
    EvaluationPeriod, ConditionalApprovalRule
)


def create_departments():
    """Create default departments"""
    departments = [
        {
            'name': 'Human Resources',
            'code': 'HR',
            'description': 'Human Resources Department'
        },
        {
            'name': 'Engineering',
            'code': 'ENG',
            'description': 'Software Engineering Department'
        },
        {
            'name': 'Marketing',
            'code': 'MKT',
            'description': 'Marketing and Communications Department'
        },
        {
            'name': 'Finance',
            'code': 'FIN',
            'description': 'Finance and Accounting Department'
        },
        {
            'name': 'Sales',
            'code': 'SALES',
            'description': 'Sales and Business Development Department'
        },
        {
            'name': 'Operations',
            'code': 'OPS',
            'description': 'Operations and Administration Department'
        },
        {
            'name': 'Customer Support',
            'code': 'CS',
            'description': 'Customer Support and Success Department'
        },
        {
            'name': 'Product Management',
            'code': 'PM',
            'description': 'Product Management Department'
        }
    ]
    
    created_departments = {}
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            code=dept_data['code'],
            defaults=dept_data
        )
        created_departments[dept_data['code']] = dept
        if created:
            print(f"✅ Created department: {dept.name}")
        else:
            print(f"⚠️  Department already exists: {dept.name}")
    
    return created_departments


def create_positions(departments):
    """Create default positions for each department"""
    positions_data = {
        'HR': [
            {'title': 'HR Assistant', 'staff_level': 'entry', 'contiss_level': 'CONTISS 4'},
            {'title': 'HR Officer', 'staff_level': 'junior', 'contiss_level': 'CONTISS 6'},
            {'title': 'Senior HR Officer', 'staff_level': 'senior', 'contiss_level': 'CONTISS 8'},
            {'title': 'HR Manager', 'staff_level': 'manager', 'contiss_level': 'CONTISS 10'},
            {'title': 'HR Director', 'staff_level': 'director', 'contiss_level': 'CONTISS 12'},
        ],
        'ENG': [
            {'title': 'Junior Developer', 'staff_level': 'entry', 'contiss_level': 'CONTISS 4'},
            {'title': 'Software Developer', 'staff_level': 'junior', 'contiss_level': 'CONTISS 6'},
            {'title': 'Senior Developer', 'staff_level': 'senior', 'contiss_level': 'CONTISS 8'},
            {'title': 'Tech Lead', 'staff_level': 'lead', 'contiss_level': 'CONTISS 9'},
            {'title': 'Engineering Manager', 'staff_level': 'manager', 'contiss_level': 'CONTISS 10'},
            {'title': 'CTO', 'staff_level': 'executive', 'contiss_level': 'CONTISS 15'},
        ],
        'MKT': [
            {'title': 'Marketing Assistant', 'staff_level': 'entry', 'contiss_level': 'CONTISS 4'},
            {'title': 'Marketing Officer', 'staff_level': 'junior', 'contiss_level': 'CONTISS 6'},
            {'title': 'Senior Marketing Officer', 'staff_level': 'senior', 'contiss_level': 'CONTISS 8'},
            {'title': 'Marketing Manager', 'staff_level': 'manager', 'contiss_level': 'CONTISS 10'},
        ],
        'FIN': [
            {'title': 'Accountant', 'staff_level': 'junior', 'contiss_level': 'CONTISS 6'},
            {'title': 'Senior Accountant', 'staff_level': 'senior', 'contiss_level': 'CONTISS 8'},
            {'title': 'Finance Manager', 'staff_level': 'manager', 'contiss_level': 'CONTISS 10'},
            {'title': 'CFO', 'staff_level': 'executive', 'contiss_level': 'CONTISS 15'},
        ],
        'SALES': [
            {'title': 'Sales Representative', 'staff_level': 'junior', 'contiss_level': 'CONTISS 6'},
            {'title': 'Senior Sales Representative', 'staff_level': 'senior', 'contiss_level': 'CONTISS 8'},
            {'title': 'Sales Manager', 'staff_level': 'manager', 'contiss_level': 'CONTISS 10'},
        ],
        'OPS': [
            {'title': 'Operations Assistant', 'staff_level': 'entry', 'contiss_level': 'CONTISS 4'},
            {'title': 'Operations Officer', 'staff_level': 'junior', 'contiss_level': 'CONTISS 6'},
            {'title': 'Operations Manager', 'staff_level': 'manager', 'contiss_level': 'CONTISS 10'},
        ],
        'CS': [
            {'title': 'Customer Support Representative', 'staff_level': 'entry', 'contiss_level': 'CONTISS 4'},
            {'title': 'Senior Customer Support', 'staff_level': 'senior', 'contiss_level': 'CONTISS 8'},
            {'title': 'Customer Success Manager', 'staff_level': 'manager', 'contiss_level': 'CONTISS 10'},
        ],
        'PM': [
            {'title': 'Product Analyst', 'staff_level': 'junior', 'contiss_level': 'CONTISS 6'},
            {'title': 'Product Manager', 'staff_level': 'manager', 'contiss_level': 'CONTISS 10'},
            {'title': 'Senior Product Manager', 'staff_level': 'senior', 'contiss_level': 'CONTISS 8'},
        ]
    }
    
    created_positions = {}
    for dept_code, positions in positions_data.items():
        if dept_code in departments:
            dept = departments[dept_code]
            for pos_data in positions:
                pos, created = Position.objects.get_or_create(
                    title=pos_data['title'],
                    department=dept,
                    defaults=pos_data
                )
                created_positions[f"{dept_code}_{pos_data['title']}"] = pos
                if created:
                    print(f"✅ Created position: {pos.title} in {dept.name}")
                else:
                    print(f"⚠️  Position already exists: {pos.title}")
    
    return created_positions


def create_roles():
    """Create default roles with hierarchical relationships"""
    roles_data = [
        {
            'name': 'System Administrator',
            'codename': 'system_admin',
            'description': 'Full system access and configuration',
            'role_type': 'system',
            'role_level': 'executive',
            'can_approve_evaluations': True,
            'can_create_evaluations': True,
            'can_view_analytics': True,
            'can_manage_users': True,
            'can_configure_system': True,
            'is_system_role': True,
        },
        {
            'name': 'HR Director',
            'codename': 'hr_director',
            'description': 'HR department leadership and oversight',
            'role_type': 'leadership',
            'role_level': 'director',
            'can_approve_evaluations': True,
            'can_create_evaluations': True,
            'can_view_analytics': True,
            'can_manage_users': True,
            'requires_approval': False,
        },
        {
            'name': 'HR Manager',
            'codename': 'hr_manager',
            'description': 'HR department management',
            'role_type': 'leadership',
            'role_level': 'manager',
            'can_approve_evaluations': True,
            'can_create_evaluations': True,
            'can_view_analytics': True,
            'can_manage_users': True,
            'requires_approval': True,
        },
        {
            'name': 'HR Officer',
            'codename': 'hr_officer',
            'description': 'HR operations and support',
            'role_type': 'functional',
            'role_level': 'senior',
            'can_approve_evaluations': False,
            'can_create_evaluations': True,
            'can_view_analytics': True,
            'can_manage_users': False,
            'requires_approval': True,
        },
        {
            'name': 'Department Director',
            'codename': 'dept_director',
            'description': 'Department leadership and oversight',
            'role_type': 'leadership',
            'role_level': 'director',
            'can_approve_evaluations': True,
            'can_create_evaluations': True,
            'can_view_analytics': True,
            'can_manage_users': True,
            'requires_approval': False,
        },
        {
            'name': 'Department Manager',
            'codename': 'dept_manager',
            'description': 'Department management and supervision',
            'role_type': 'leadership',
            'role_level': 'manager',
            'can_approve_evaluations': True,
            'can_create_evaluations': True,
            'can_view_analytics': True,
            'can_manage_users': True,
            'requires_approval': True,
        },
        {
            'name': 'Team Lead',
            'codename': 'team_lead',
            'description': 'Team leadership and coordination',
            'role_type': 'leadership',
            'role_level': 'lead',
            'can_approve_evaluations': True,
            'can_create_evaluations': True,
            'can_view_analytics': True,
            'can_manage_users': False,
            'requires_approval': True,
        },
        {
            'name': 'Senior Staff',
            'codename': 'senior_staff',
            'description': 'Senior level staff member',
            'role_type': 'functional',
            'role_level': 'senior',
            'can_approve_evaluations': False,
            'can_create_evaluations': False,
            'can_view_analytics': False,
            'can_manage_users': False,
            'requires_approval': False,
        },
        {
            'name': 'Junior Staff',
            'codename': 'junior_staff',
            'description': 'Junior level staff member',
            'role_type': 'functional',
            'role_level': 'junior',
            'can_approve_evaluations': False,
            'can_create_evaluations': False,
            'can_view_analytics': False,
            'can_manage_users': False,
            'requires_approval': False,
        },
        {
            'name': 'Entry Level Staff',
            'codename': 'entry_staff',
            'description': 'Entry level staff member',
            'role_type': 'functional',
            'role_level': 'entry',
            'can_approve_evaluations': False,
            'can_create_evaluations': False,
            'can_view_analytics': False,
            'can_manage_users': False,
            'requires_approval': False,
        }
    ]
    
    created_roles = {}
    for role_data in roles_data:
        role, created = Role.objects.get_or_create(
            codename=role_data['codename'],
            defaults=role_data
        )
        created_roles[role_data['codename']] = role
        if created:
            print(f"✅ Created role: {role.name}")
        else:
            print(f"⚠️  Role already exists: {role.name}")
    
    # Set up role hierarchy relationships
    setup_role_hierarchy(created_roles)
    
    return created_roles


def setup_role_hierarchy(roles):
    """Set up role hierarchy and management relationships"""
    # System Admin can manage all roles
    system_admin = roles.get('system_admin')
    if system_admin:
        for role in roles.values():
            if role != system_admin:
                system_admin.can_manage_roles.add(role)
                system_admin.can_create_kpis_for.add(role)
                system_admin.can_evaluate_roles.add(role)
    
    # HR Director can manage HR roles and evaluate all
    hr_director = roles.get('hr_director')
    if hr_director:
        hr_roles = [roles.get('hr_manager'), roles.get('hr_officer')]
        for role in hr_roles:
            if role:
                hr_director.can_manage_roles.add(role)
                hr_director.can_create_kpis_for.add(role)
        # HR Director can evaluate all roles
        for role in roles.values():
            if role != hr_director:
                hr_director.can_evaluate_roles.add(role)
    
    # HR Manager can manage HR Officer
    hr_manager = roles.get('hr_manager')
    hr_officer = roles.get('hr_officer')
    if hr_manager and hr_officer:
        hr_manager.can_manage_roles.add(hr_officer)
        hr_manager.can_create_kpis_for.add(hr_officer)
        hr_manager.can_evaluate_roles.add(hr_officer)
    
    # Department Director can manage department roles
    dept_director = roles.get('dept_director')
    if dept_director:
        dept_roles = [roles.get('dept_manager'), roles.get('team_lead'), roles.get('senior_staff'), roles.get('junior_staff'), roles.get('entry_staff')]
        for role in dept_roles:
            if role:
                dept_director.can_manage_roles.add(role)
                dept_director.can_create_kpis_for.add(role)
                dept_director.can_evaluate_roles.add(role)
    
    # Department Manager can manage team roles
    dept_manager = roles.get('dept_manager')
    if dept_manager:
        team_roles = [roles.get('team_lead'), roles.get('senior_staff'), roles.get('junior_staff'), roles.get('entry_staff')]
        for role in team_roles:
            if role:
                dept_manager.can_manage_roles.add(role)
                dept_manager.can_create_kpis_for.add(role)
                dept_manager.can_evaluate_roles.add(role)
    
    # Team Lead can manage junior staff
    team_lead = roles.get('team_lead')
    if team_lead:
        junior_roles = [roles.get('senior_staff'), roles.get('junior_staff'), roles.get('entry_staff')]
        for role in junior_roles:
            if role:
                team_lead.can_manage_roles.add(role)
                team_lead.can_create_kpis_for.add(role)
                team_lead.can_evaluate_roles.add(role)
    
    print("✅ Role hierarchy relationships configured")


def create_evaluation_questions():
    """Create default evaluation questions for different roles and levels"""
    questions_data = [
        # Personal Data Questions
        {
            'question_text': 'What is your current job title and department?',
            'section': 'personal_data',
            'question_type': 'text',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'How long have you been in your current position?',
            'section': 'personal_data',
            'question_type': 'number',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 2,
        },
        
        # Qualifications Questions
        {
            'question_text': 'List your relevant qualifications and certifications',
            'section': 'qualifications',
            'question_type': 'textarea',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'What professional development activities have you completed this year?',
            'section': 'qualifications',
            'question_type': 'textarea',
            'target_staff_levels': ['mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 2,
        },
        
        # Training Questions
        {
            'question_text': 'What training programs have you attended this year?',
            'section': 'training',
            'question_type': 'textarea',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'What additional training do you need for your role?',
            'section': 'training',
            'question_type': 'textarea',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': False,
            'order': 2,
        },
        
        # Responsibilities Questions
        {
            'question_text': 'Describe your key responsibilities and duties',
            'section': 'responsibilities',
            'question_type': 'textarea',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'What are your main achievements this year?',
            'section': 'responsibilities',
            'question_type': 'textarea',
            'target_staff_levels': ['mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 2,
        },
        
        # Leadership Questions (for management roles)
        {
            'question_text': 'How do you motivate and lead your team?',
            'section': 'leadership',
            'question_type': 'textarea',
            'target_staff_levels': ['lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'Describe a challenging leadership situation you handled',
            'section': 'leadership',
            'question_type': 'textarea',
            'target_staff_levels': ['manager', 'director', 'executive'],
            'required': True,
            'order': 2,
        },
        
        # Teamwork Questions
        {
            'question_text': 'How do you contribute to team success?',
            'section': 'teamwork',
            'question_type': 'textarea',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'Rate your teamwork skills (1-5)',
            'section': 'teamwork',
            'question_type': 'rating',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 2,
            'options': '1\n2\n3\n4\n5',
            'scoring_criteria': {'max_rating': 5},
        },
        
        # Technical Skills Questions (for technical roles)
        {
            'question_text': 'What technical skills have you developed this year?',
            'section': 'technical_skills',
            'question_type': 'textarea',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'Rate your technical proficiency (1-5)',
            'section': 'technical_skills',
            'question_type': 'rating',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager'],
            'required': True,
            'order': 2,
            'options': '1\n2\n3\n4\n5',
            'scoring_criteria': {'max_rating': 5},
        },
        
        # Communication Questions
        {
            'question_text': 'How do you ensure effective communication with stakeholders?',
            'section': 'communication',
            'question_type': 'textarea',
            'target_staff_levels': ['mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'Rate your communication skills (1-5)',
            'section': 'communication',
            'question_type': 'rating',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 2,
            'options': '1\n2\n3\n4\n5',
            'scoring_criteria': {'max_rating': 5},
        },
        
        # Goals Questions
        {
            'question_text': 'What are your short-term goals (next 6 months)?',
            'section': 'goals',
            'question_type': 'textarea',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
        },
        {
            'question_text': 'What are your long-term career goals?',
            'section': 'goals',
            'question_type': 'textarea',
            'target_staff_levels': ['mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 2,
        },
        
        # Performance Questions
        {
            'question_text': 'Rate your overall performance this year (1-5)',
            'section': 'performance',
            'question_type': 'rating',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 1,
            'options': '1\n2\n3\n4\n5',
            'scoring_criteria': {'max_rating': 5},
        },
        {
            'question_text': 'What areas do you need to improve?',
            'section': 'performance',
            'question_type': 'textarea',
            'target_staff_levels': ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive'],
            'required': True,
            'order': 2,
        },
    ]
    
    for question_data in questions_data:
        question, created = EvaluationQuestion.objects.get_or_create(
            question_text=question_data['question_text'],
            section=question_data['section'],
            defaults=question_data
        )
        if created:
            print(f"✅ Created question: {question.question_text[:50]}...")
        else:
            print(f"⚠️  Question already exists: {question.question_text[:50]}...")


def create_kpi_templates():
    """Create default KPI templates for different roles"""
    kpis_data = [
        # General KPIs
        {
            'name': 'Attendance Rate',
            'description': 'Percentage of days present at work',
            'kpi_type': 'percentage',
            'visibility': 'all',
            'unit_of_measure': '%',
            'min_value': 0,
            'max_value': 100,
            'target_value': 95,
            'scoring_method': 'threshold',
            'is_auto_calculated': True,
            'data_source': 'attendance_system',
        },
        {
            'name': 'Task Completion Rate',
            'description': 'Percentage of assigned tasks completed on time',
            'kpi_type': 'percentage',
            'visibility': 'all',
            'unit_of_measure': '%',
            'min_value': 0,
            'max_value': 100,
            'target_value': 90,
            'scoring_method': 'linear',
        },
        
        # Technical KPIs (for engineering roles)
        {
            'name': 'Code Quality Score',
            'description': 'Code quality rating from code reviews',
            'kpi_type': 'rating',
            'visibility': 'role',
            'unit_of_measure': 'score',
            'min_value': 1,
            'max_value': 5,
            'target_value': 4,
            'scoring_method': 'linear',
        },
        {
            'name': 'Bug Resolution Time',
            'description': 'Average time to resolve bugs in hours',
            'kpi_type': 'duration',
            'visibility': 'role',
            'unit_of_measure': 'hours',
            'target_value': 24,
            'scoring_method': 'threshold',
        },
        
        # Sales KPIs
        {
            'name': 'Sales Target Achievement',
            'description': 'Percentage of sales target achieved',
            'kpi_type': 'percentage',
            'visibility': 'role',
            'unit_of_measure': '%',
            'min_value': 0,
            'max_value': 200,
            'target_value': 100,
            'scoring_method': 'linear',
        },
        {
            'name': 'Customer Acquisition Cost',
            'description': 'Cost to acquire new customers',
            'kpi_type': 'currency',
            'visibility': 'role',
            'unit_of_measure': 'USD',
            'target_value': 100,
            'scoring_method': 'threshold',
        },
        
        # Customer Support KPIs
        {
            'name': 'Customer Satisfaction Score',
            'description': 'Average customer satisfaction rating',
            'kpi_type': 'rating',
            'visibility': 'role',
            'unit_of_measure': 'score',
            'min_value': 1,
            'max_value': 5,
            'target_value': 4.5,
            'scoring_method': 'linear',
        },
        {
            'name': 'Response Time',
            'description': 'Average response time to customer inquiries',
            'kpi_type': 'duration',
            'visibility': 'role',
            'unit_of_measure': 'hours',
            'target_value': 2,
            'scoring_method': 'threshold',
        },
        
        # Management KPIs
        {
            'name': 'Team Performance',
            'description': 'Average team member performance score',
            'kpi_type': 'rating',
            'visibility': 'level',
            'unit_of_measure': 'score',
            'min_value': 1,
            'max_value': 5,
            'target_value': 4,
            'scoring_method': 'linear',
        },
        {
            'name': 'Project Delivery Rate',
            'description': 'Percentage of projects delivered on time',
            'kpi_type': 'percentage',
            'visibility': 'level',
            'unit_of_measure': '%',
            'min_value': 0,
            'max_value': 100,
            'target_value': 95,
            'scoring_method': 'linear',
        },
    ]
    
    for kpi_data in kpis_data:
        kpi, created = KPITemplate.objects.get_or_create(
            name=kpi_data['name'],
            defaults=kpi_data
        )
        if created:
            print(f"✅ Created KPI: {kpi.name}")
        else:
            print(f"⚠️  KPI already exists: {kpi.name}")


def create_evaluation_periods():
    """Create default evaluation periods"""
    periods_data = [
        {
            'name': 'Q1 2024 Performance Review',
            'start_date': datetime(2024, 1, 1).date(),
            'end_date': datetime(2024, 3, 31).date(),
            'submission_deadline': timezone.now() + timedelta(days=30),
            'is_open_for_submission': True,
            'description': 'First quarter performance review period',
        },
        {
            'name': 'Q2 2024 Performance Review',
            'start_date': datetime(2024, 4, 1).date(),
            'end_date': datetime(2024, 6, 30).date(),
            'submission_deadline': timezone.now() + timedelta(days=120),
            'is_open_for_submission': False,
            'description': 'Second quarter performance review period',
        },
    ]
    
    for period_data in periods_data:
        period, created = EvaluationPeriod.objects.get_or_create(
            name=period_data['name'],
            defaults=period_data
        )
        if created:
            print(f"✅ Created evaluation period: {period.name}")
        else:
            print(f"⚠️  Evaluation period already exists: {period.name}")


def create_system_configurations():
    """Create default system configurations"""
    configs = [
        {
            'key': 'evaluation_period_duration',
            'value': '90',
            'description': 'Duration of evaluation periods in days'
        },
        {
            'key': 'max_goals_per_user',
            'value': '10',
            'description': 'Maximum number of goals a user can have'
        },
        {
            'key': 'kpi_auto_calculation_frequency',
            'value': 'monthly',
            'description': 'Frequency of automatic KPI calculations'
        },
        {
            'key': 'evaluation_approval_required',
            'value': 'true',
            'description': 'Whether evaluations require approval'
        },
        {
            'key': 'notification_enabled',
            'value': 'true',
            'description': 'Enable system notifications'
        },
        {
            'key': 'max_file_upload_size',
            'value': '10',
            'description': 'Maximum file upload size in MB'
        },
    ]
    
    for config_data in configs:
        config, created = SystemConfiguration.objects.get_or_create(
            key=config_data['key'],
            defaults=config_data
        )
        if created:
            print(f"✅ Created system config: {config.key}")
        else:
            print(f"⚠️  System config already exists: {config.key}")


def create_superuser():
    """Create a default superuser if none exists"""
    if not User.objects.filter(is_superuser=True).exists():
        user = User.objects.create_superuser(
            username='admin',
            email='admin@apes.techonstreet.com',
            password='admin123'
        )
        print(f"✅ Created superuser: {user.username}")
        return user
    else:
        print("⚠️  Superuser already exists")
        return User.objects.filter(is_superuser=True).first()


def main():
    """Main function to run all seed data creation"""
    print("🌱 Starting seed data creation...")
    
    # Create departments
    print("\n📋 Creating departments...")
    departments = create_departments()
    
    # Create positions
    print("\n👥 Creating positions...")
    positions = create_positions(departments)
    
    # Create roles
    print("\n🎭 Creating roles...")
    roles = create_roles()
    
    # Create evaluation questions
    print("\n❓ Creating evaluation questions...")
    create_evaluation_questions()
    
    # Create KPI templates
    print("\n📊 Creating KPI templates...")
    create_kpi_templates()
    
    # Create evaluation periods
    print("\n📅 Creating evaluation periods...")
    create_evaluation_periods()
    
    # Create system configurations
    print("\n⚙️  Creating system configurations...")
    create_system_configurations()
    
    # Create superuser
    print("\n👑 Creating superuser...")
    create_superuser()
    
    print("\n✅ Seed data creation completed successfully!")
    print("\n📝 Summary:")
    print(f"   - Departments: {Department.objects.count()}")
    print(f"   - Positions: {Position.objects.count()}")
    print(f"   - Roles: {Role.objects.count()}")
    print(f"   - Evaluation Questions: {EvaluationQuestion.objects.count()}")
    print(f"   - KPI Templates: {KPITemplate.objects.count()}")
    print(f"   - Evaluation Periods: {EvaluationPeriod.objects.count()}")
    print(f"   - System Configurations: {SystemConfiguration.objects.count()}")
    print(f"   - Users: {User.objects.count()}")


if __name__ == '__main__':
    main() 