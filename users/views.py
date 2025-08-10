from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
import json
import csv
from datetime import datetime, timedelta

from .models import (
    StaffRegistration, UserProfile, StaffDocument, StaffBankDetails,
    StaffPensionDetails, StaffTaxDetails, StaffMedicalDetails, StaffAuditLog,
    SupervisorRelationship, ProfileUpdateRequest, StaffQualification,
    ActingAppointment, StaffTraining
)
from .serializers import (
    StaffRegistrationSerializer, StaffRegistrationCreateSerializer,
    StaffRegistrationUpdateSerializer, UserProfileSerializer,
    StaffDocumentSerializer, StaffBankDetailsSerializer, StaffPensionDetailsSerializer,
    StaffTaxDetailsSerializer, StaffMedicalDetailsSerializer, StaffAuditLogSerializer,
    SupervisorRelationshipSerializer, ProfileUpdateRequestSerializer,
    StaffQualificationSerializer, ActingAppointmentSerializer, StaffTrainingSerializer,
    PasswordChangeSerializer, PasswordResetSerializer, BulkStaffRegistrationSerializer,
    StaffStatisticsSerializer
)
from notifications.services import action_notification_service


@login_required
def staff_list(request):
    """API endpoint for staff list"""
    try:
        staff_list = StaffRegistration.objects.filter(is_active=True).select_related('department', 'position')
        
        # Filtering
        department = request.GET.get('department')
        if department:
            staff_list = staff_list.filter(department__name__icontains=department)
        
        position = request.GET.get('position')
        if position:
            staff_list = staff_list.filter(position__name__icontains=position)
        
        search = request.GET.get('search')
        if search:
            staff_list = staff_list.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(staff_list, 20)
        staff_page = paginator.get_page(page)
        
        serializer = StaffRegistrationSerializer(staff_page, many=True)
        
        return JsonResponse({
            'status': 'success',
            'data': serializer.data,
            'pagination': {
                'current_page': staff_page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': staff_page.has_next(),
                'has_previous': staff_page.has_previous()
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def register_staff(request):
    """API endpoint for staff registration"""
    try:
        data = json.loads(request.body)
        serializer = StaffRegistrationCreateSerializer(data=data)
        
        if serializer.is_valid():
            staff_data = serializer.validated_data
            
            # Create Django User
            user = User.objects.create_user(
                username=staff_data['username'],
                email=staff_data['email'],
                password=staff_data.get('password', 'National2025'),
                first_name=staff_data['first_name'],
                last_name=staff_data['last_name']
            )
            
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                phone_number=staff_data.get('phone_number'),
                address=staff_data.get('address'),
                date_of_birth=staff_data.get('date_of_birth'),
                gender=staff_data.get('gender'),
                emergency_contact_name=staff_data.get('emergency_contact_name'),
                emergency_contact_phone=staff_data.get('emergency_contact_phone'),
                next_of_kin_name=staff_data.get('next_of_kin_name'),
                next_of_kin_phone=staff_data.get('next_of_kin_phone'),
                next_of_kin_relationship=staff_data.get('next_of_kin_relationship')
            )
            
            # Save staff registration
            staff_reg = serializer.save(user=user)
            
            # Send notification
            action_notification_service.staff_registration_notification(user, staff_data)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Staff registered successfully',
                'data': StaffRegistrationSerializer(staff_reg).data
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def staff_detail(request, staff_id):
    """API endpoint for staff detail"""
    try:
        staff = get_object_or_404(StaffRegistration, id=staff_id)
        serializer = StaffRegistrationSerializer(staff)
        
        return JsonResponse({
            'status': 'success',
            'data': serializer.data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["PUT", "PATCH"])
def edit_staff(request, staff_id):
    """API endpoint for editing staff"""
    try:
        staff = get_object_or_404(StaffRegistration, id=staff_id)
        data = json.loads(request.body)
        
        serializer = StaffRegistrationUpdateSerializer(staff, data=data, partial=True)
        if serializer.is_valid():
            updated_staff = serializer.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Staff updated successfully',
                'data': StaffRegistrationSerializer(updated_staff).data
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def reset_password(request, staff_id):
    """API endpoint for password reset"""
    try:
        staff = get_object_or_404(StaffRegistration, id=staff_id)
        user = staff.user
        
        # Reset password
        user.password = make_password('National2025')
        user.save()
        
        # Send notification
        action_notification_service.password_reset_notification(user, 'National2025')
        
        return JsonResponse({
            'status': 'success',
            'message': 'Password reset successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def change_password(request, staff_id):
    """API endpoint for password change"""
    try:
        staff = get_object_or_404(StaffRegistration, id=staff_id)
        user = staff.user
        
        data = json.loads(request.body)
        serializer = PasswordChangeSerializer(data=data)
        
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            user.password = make_password(new_password)
            user.save()
            
            # Send notification
            action_notification_service.password_reset_notification(user, new_password)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Password changed successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def bulk_register_staff(request):
    """API endpoint for bulk staff registration"""
    try:
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return JsonResponse({
                'status': 'error',
                'message': 'CSV file is required'
            }, status=400)
        
        # Read CSV file
        csv_data = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(csv_data.splitlines())
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row in csv_reader:
            try:
                # Create user
                user = User.objects.create_user(
                    username=row['username'],
                    email=row['email'],
                    password='National2025',
                    first_name=row.get('first_name', ''),
                    last_name=row.get('last_name', '')
                )
                
                # Create staff registration
                staff_data = {
                    'user': user,
                    'employee_id': row['employee_id'],
                    'first_name': row.get('first_name', ''),
                    'last_name': row.get('last_name', ''),
                    'email': row['email'],
                    'username': row['username'],
                    'phone_number': row.get('phone_number', ''),
                    'department_id': row.get('department_id'),
                    'position_id': row.get('position_id'),
                    'employment_status': row.get('employment_status', 'active'),
                    'date_of_appointment': row.get('date_of_appointment'),
                    'is_active': True
                }
                
                staff = StaffRegistration.objects.create(**staff_data)
                
                # Send notification
                action_notification_service.staff_registration_notification(user, staff_data)
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {success_count + error_count}: {str(e)}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Bulk registration completed. Success: {success_count}, Errors: {error_count}',
            'data': {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def staff_analytics(request):
    """API endpoint for staff analytics"""
    try:
        total_staff = StaffRegistration.objects.count()
        active_staff = StaffRegistration.objects.filter(is_active=True).count()
        inactive_staff = StaffRegistration.objects.filter(is_active=False).count()
        
        # Department distribution
        dept_distribution = StaffRegistration.objects.values('department__name').annotate(
            count=Count('id')
        )
        
        # Position distribution
        pos_distribution = StaffRegistration.objects.values('position__name').annotate(
            count=Count('id')
        )
        
        # Gender distribution
        gender_distribution = StaffRegistration.objects.values('gender').annotate(
            count=Count('id')
        )
        
        # Recent registrations (last 30 days)
        recent_registrations = StaffRegistration.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        data = {
            'total_staff': total_staff,
            'active_staff': active_staff,
            'inactive_staff': inactive_staff,
            'department_distribution': {item['department__name']: item['count'] for item in dept_distribution},
            'position_distribution': {item['position__name']: item['count'] for item in pos_distribution},
            'gender_distribution': {item['gender']: item['count'] for item in gender_distribution},
            'recent_registrations': recent_registrations
        }
        
        return JsonResponse({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def export_staff_data(request):
    """API endpoint for exporting staff data"""
    try:
        staff_list = StaffRegistration.objects.all()
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="staff_data.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'First Name', 'Last Name', 'Email', 'Username',
            'Phone Number', 'Department', 'Position', 'Employment Status',
            'Date of Appointment', 'Is Active'
        ])
        
        for staff in staff_list:
            writer.writerow([
                staff.employee_id,
                staff.first_name,
                staff.last_name,
                staff.email,
                staff.username,
                staff.phone_number,
                staff.department.name if staff.department else '',
                staff.position.name if staff.position else '',
                staff.employment_status,
                staff.date_of_appointment,
                staff.is_active
            ])
        
        return response
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def check_username_availability(request):
    """API endpoint for checking username availability"""
    try:
        username = request.GET.get('username')
        if not username:
            return JsonResponse({
                'status': 'error',
                'message': 'Username parameter is required'
            }, status=400)
        
        is_available = not User.objects.filter(username=username).exists()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'username': username,
                'available': is_available
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def check_email_availability(request):
    """API endpoint for checking email availability"""
    try:
        email = request.GET.get('email')
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Email parameter is required'
            }, status=400)
        
        is_available = not User.objects.filter(email=email).exists()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'email': email,
                'available': is_available
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def check_employee_id_availability(request):
    """API endpoint for checking employee ID availability"""
    try:
        employee_id = request.GET.get('employee_id')
        if not employee_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Employee ID parameter is required'
            }, status=400)
        
        is_available = not StaffRegistration.objects.filter(employee_id=employee_id).exists()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'employee_id': employee_id,
                'available': is_available
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
