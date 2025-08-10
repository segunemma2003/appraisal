#!/usr/bin/env python3
"""
Data seeding script for APES system
Run this script to populate the database with initial data
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Department, Position, SystemConfiguration
from evaluations.models import EvaluationQuestion, PerformanceAspect, EvaluationPeriod


def create_sample_data():
    """Create sample departments and positions"""
    print("Creating sample data...")
    
    # Create departments
    departments = [
        {'name': 'Administration', 'code': 'ADMIN'},
        {'name': 'Research & Development', 'code': 'RND'},
        {'name': 'Engineering', 'code': 'ENG'},
        {'name': 'Human Resources', 'code': 'HR'},
        {'name': 'Information Technology', 'code': 'IT'},
    ]
    
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            code=dept_data['code'],
            defaults=dept_data
        )
        if created:
            print(f"Created department: {dept.name}")
    
    # Create positions
    positions = [
        {'title': 'Director', 'staff_level': 'senior', 'contiss_level': 'CONTISS 15'},
        {'title': 'Deputy Director', 'staff_level': 'senior', 'contiss_level': 'CONTISS 14'},
        {'title': 'Assistant Director', 'staff_level': 'senior', 'contiss_level': 'CONTISS 13'},
        {'title': 'Principal Officer', 'staff_level': 'senior', 'contiss_level': 'CONTISS 12'},
        {'title': 'Senior Officer', 'staff_level': 'senior', 'contiss_level': 'CONTISS 11'},
        {'title': 'Officer I', 'staff_level': 'senior', 'contiss_level': 'CONTISS 10'},
        {'title': 'Officer II', 'staff_level': 'senior', 'contiss_level': 'CONTISS 09'},
        {'title': 'Assistant Officer', 'staff_level': 'junior', 'contiss_level': 'CONTISS 08'},
        {'title': 'Senior Assistant', 'staff_level': 'junior', 'contiss_level': 'CONTISS 07'},
        {'title': 'Assistant', 'staff_level': 'junior', 'contiss_level': 'CONTISS 06'},
    ]
    
    admin_dept = Department.objects.get(code='ADMIN')
    for pos_data in positions:
        pos, created = Position.objects.get_or_create(
            title=pos_data['title'],
            defaults={**pos_data, 'department': admin_dept}
        )
        if created:
            print(f"Created position: {pos.title}")
    
    # Create system configurations
    configs = [
        ('evaluation_submission_enabled', 'false', 'Whether evaluation submission is currently enabled'),
        ('profile_update_enabled', 'false', 'Whether profile updates are currently enabled'),
        ('default_approval_workflow', 'standard', 'Default approval workflow for evaluations'),
        ('max_file_size_mb', '10', 'Maximum file size for uploads in MB'),
        ('evaluation_deadline_reminder_days', '7', 'Days before deadline to send reminders'),
    ]
    
    for key, value, description in configs:
        config, created = SystemConfiguration.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if created:
            print(f"Created configuration: {key}")
    
    print("Sample data created successfully!")


def create_evaluation_questions():
    """Create evaluation questions and performance aspects"""
    print("Creating evaluation questions...")
    
    # Clear existing questions and aspects
    EvaluationQuestion.objects.all().delete()
    PerformanceAspect.objects.all().delete()
    
    # Performance Aspects for both staff levels
    performance_aspects = [
        {'name': 'Quality of Work', 'description': 'Accuracy, thoroughness, and reliability of work output'},
        {'name': 'Quantity of Work', 'description': 'Volume of work produced and efficiency'},
        {'name': 'Dependability', 'description': 'Reliability, punctuality, and consistency'},
        {'name': 'Initiative', 'description': 'Self-motivation and proactive approach to work'},
        {'name': 'Cooperation', 'description': 'Teamwork and ability to work with others'},
        {'name': 'Communication Skills', 'description': 'Verbal and written communication effectiveness'},
        {'name': 'Problem Solving', 'description': 'Analytical thinking and problem-solving abilities'},
        {'name': 'Leadership', 'description': 'Ability to lead and motivate others (for senior staff)'},
        {'name': 'Technical Skills', 'description': 'Professional and technical competence'},
        {'name': 'Adaptability', 'description': 'Flexibility and ability to handle change'},
    ]
    
    for aspect_data in performance_aspects:
        aspect, created = PerformanceAspect.objects.get_or_create(
            name=aspect_data['name'],
            defaults=aspect_data
        )
        if created:
            print(f'Created performance aspect: {aspect.name}')
    
    # Evaluation Questions for Junior Staff
    junior_questions = [
        # Personal Data Section
        {
            'question_text': 'Surname',
            'section': 'personal_data',
            'staff_level': 'junior',
            'question_type': 'text',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'First Name',
            'section': 'personal_data',
            'staff_level': 'junior',
            'question_type': 'text',
            'required': True,
            'order': 2
        },
        {
            'question_text': 'Middle Name',
            'section': 'personal_data',
            'staff_level': 'junior',
            'question_type': 'text',
            'required': False,
            'order': 3
        },
        {
            'question_text': 'Title (Mr./Mrs./Ms./Dr.)',
            'section': 'personal_data',
            'staff_level': 'junior',
            'question_type': 'text',
            'required': True,
            'order': 4
        },
        {
            'question_text': 'Date of Birth',
            'section': 'personal_data',
            'staff_level': 'junior',
            'question_type': 'date',
            'required': True,
            'order': 5
        },
        {
            'question_text': 'Marital Status',
            'section': 'personal_data',
            'staff_level': 'junior',
            'question_type': 'select',
            'options': 'single,married,divorced,widowed',
            'required': True,
            'order': 6
        },
        
        # Qualifications Section
        {
            'question_text': 'List your academic qualifications',
            'section': 'qualifications',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'Professional qualifications and certifications',
            'section': 'qualifications',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': False,
            'order': 2
        },
        
        # Training Section
        {
            'question_text': 'Training programs attended in the last year',
            'section': 'training',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'Skills acquired from training',
            'section': 'training',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
        
        # Responsibilities Section
        {
            'question_text': 'Describe your main responsibilities and duties',
            'section': 'responsibilities',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'Key achievements in the last year',
            'section': 'responsibilities',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
        
        # Challenges Section
        {
            'question_text': 'Major challenges faced in your role',
            'section': 'challenges',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'How you overcame these challenges',
            'section': 'challenges',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
        
        # Goals Section
        {
            'question_text': 'Goals for the next evaluation period',
            'section': 'goals',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'Training needs for career development',
            'section': 'goals',
            'staff_level': 'junior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
    ]
    
    # Evaluation Questions for Senior Staff
    senior_questions = [
        # Personal Data Section (same as junior)
        {
            'question_text': 'Surname',
            'section': 'personal_data',
            'staff_level': 'senior',
            'question_type': 'text',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'First Name',
            'section': 'personal_data',
            'staff_level': 'senior',
            'question_type': 'text',
            'required': True,
            'order': 2
        },
        {
            'question_text': 'Middle Name',
            'section': 'personal_data',
            'staff_level': 'senior',
            'question_type': 'text',
            'required': False,
            'order': 3
        },
        {
            'question_text': 'Title (Mr./Mrs./Ms./Dr.)',
            'section': 'personal_data',
            'staff_level': 'senior',
            'question_type': 'text',
            'required': True,
            'order': 4
        },
        {
            'question_text': 'Date of Birth',
            'section': 'personal_data',
            'staff_level': 'senior',
            'question_type': 'date',
            'required': True,
            'order': 5
        },
        {
            'question_text': 'Marital Status',
            'section': 'personal_data',
            'staff_level': 'senior',
            'question_type': 'select',
            'options': 'single,married,divorced,widowed',
            'required': True,
            'order': 6
        },
        
        # Qualifications Section
        {
            'question_text': 'List your academic qualifications',
            'section': 'qualifications',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'Professional qualifications and certifications',
            'section': 'qualifications',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
        {
            'question_text': 'Research publications and contributions',
            'section': 'qualifications',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 3
        },
        
        # Training Section
        {
            'question_text': 'Training programs attended in the last year',
            'section': 'training',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'Skills acquired from training',
            'section': 'training',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
        {
            'question_text': 'Training programs conducted for others',
            'section': 'training',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': False,
            'order': 3
        },
        
        # Responsibilities Section
        {
            'question_text': 'Describe your main responsibilities and duties',
            'section': 'responsibilities',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'Key achievements in the last year',
            'section': 'responsibilities',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
        {
            'question_text': 'Leadership and management achievements',
            'section': 'responsibilities',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 3
        },
        {
            'question_text': 'Research and development contributions',
            'section': 'responsibilities',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 4
        },
        
        # Challenges Section
        {
            'question_text': 'Major challenges faced in your role',
            'section': 'challenges',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'How you overcame these challenges',
            'section': 'challenges',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
        {
            'question_text': 'Strategic challenges and solutions',
            'section': 'challenges',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 3
        },
        
        # Goals Section
        {
            'question_text': 'Goals for the next evaluation period',
            'section': 'goals',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 1
        },
        {
            'question_text': 'Training needs for career development',
            'section': 'goals',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 2
        },
        {
            'question_text': 'Strategic objectives for the department/organization',
            'section': 'goals',
            'staff_level': 'senior',
            'question_type': 'textarea',
            'required': True,
            'order': 3
        },
    ]
    
    # Create questions for both staff levels
    all_questions = junior_questions + senior_questions
    
    for question_data in all_questions:
        question, created = EvaluationQuestion.objects.get_or_create(
            question_text=question_data['question_text'],
            section=question_data['section'],
            staff_level=question_data['staff_level'],
            defaults=question_data
        )
        if created:
            print(f'Created question: {question.question_text} ({question.staff_level})')
    
    print(f'Successfully created {len(all_questions)} evaluation questions and {len(performance_aspects)} performance aspects!')


def create_evaluation_period():
    """Create a sample evaluation period"""
    print("Creating sample evaluation period...")
    
    period, created = EvaluationPeriod.objects.get_or_create(
        name="Annual Evaluation 2024",
        defaults={
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'is_active': True,
            'is_open_for_submission': False,
        }
    )
    
    if created:
        print(f"Created evaluation period: {period.name}")
    else:
        print(f"Evaluation period already exists: {period.name}")


def main():
    """Main function to run all seeding operations"""
    print("=" * 60)
    print("APES (Automated Annual Performance Evaluation System)")
    print("Data Seeding Script")
    print("=" * 60)
    
    try:
        # Create sample data
        create_sample_data()
        
        # Create evaluation questions
        create_evaluation_questions()
        
        # Create evaluation period
        create_evaluation_period()
        
        print("\n" + "=" * 60)
        print("Data seeding completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run the development server: python manage.py runserver")
        print("2. Access the admin interface: http://localhost:8000/admin/")
        print("3. Access the API: http://localhost:8000/api/v1/")
        print("4. Check the README.md for detailed documentation")
        
    except Exception as e:
        print(f"\nError during data seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main() 