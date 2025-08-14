# Complete API Documentation - Dynamic Role-Based Appraisal System

## Overview

This document provides comprehensive API documentation for the Dynamic Role-Based Appraisal System. The system implements granular permissions, dynamic questions, and role-based access control.

## Base URL

```
https://apes.techonstreet.com/api/
```

## Authentication

All APIs require authentication using JWT tokens or session-based authentication.

## Core System APIs

### 1. Role Management

#### List and Create Roles

```http
GET /core/roles/
POST /core/roles/
```

**GET Response:**

```json
{
  "roles": [
    {
      "id": 1,
      "name": "HR Manager",
      "codename": "hr_manager",
      "description": "Human Resources Manager role",
      "role_type": "department",
      "department": "Human Resources",
      "is_system_role": false,
      "permissions_count": 15,
      "users_count": 3,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_pages": 5,
  "current_page": 1
}
```

**POST Request:**

```json
{
  "name": "Senior Developer",
  "codename": "senior_dev",
  "description": "Senior software developer role",
  "role_type": "department",
  "department_id": 2,
  "is_system_role": false,
  "permissions": [
    {
      "permission_id": 5,
      "conditions": { "department_id": 2 }
    }
  ]
}
```

#### Get, Update, Delete Role

```http
GET /core/roles/{role_id}/
PUT /core/roles/{role_id}/
DELETE /core/roles/{role_id}/
```

### 2. Permission Management

#### List and Create Permissions

```http
GET /core/permissions/
POST /core/permissions/
```

**GET Response:**

```json
{
  "permissions": [
    {
      "id": 1,
      "codename": "create_evaluation",
      "name": "Create Evaluation",
      "description": "Can create new evaluation forms",
      "permission_type": "create",
      "resource_type": "evaluation",
      "department_scope": "Human Resources",
      "is_system_permission": true,
      "roles_count": 3,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**POST Request:**

```json
{
  "codename": "approve_goals",
  "name": "Approve Goals",
  "description": "Can approve employee goals",
  "permission_type": "approve",
  "resource_type": "goal",
  "department_scope_id": 2,
  "is_system_permission": false
}
```

#### Get Permission Choices

```http
GET /core/permissions/choices/
```

**Response:**

```json
{
  "permission_types": [
    ["create", "Create"],
    ["read", "Read"],
    ["update", "Update"],
    ["delete", "Delete"],
    ["approve", "Approve"],
    ["reject", "Reject"],
    ["export", "Export"],
    ["import", "Import"],
    ["assign", "Assign"],
    ["delegate", "Delegate"],
    ["override", "Override"],
    ["view_analytics", "View Analytics"],
    ["manage_users", "Manage Users"],
    ["configure_system", "Configure System"]
  ],
  "resource_types": [
    ["evaluation", "Evaluation"],
    ["kpi", "KPI"],
    ["form_template", "Form Template"],
    ["goal", "Goal"],
    ["approval", "Approval"],
    ["analytics", "Analytics"],
    ["user", "User"],
    ["department", "Department"],
    ["role", "Role"],
    ["permission", "Permission"],
    ["system_config", "System Configuration"],
    ["audit_log", "Audit Log"],
    ["notification", "Notification"],
    ["report", "Report"]
  ],
  "role_types": [
    ["system", "System Role"],
    ["department", "Department Role"],
    ["project", "Project Role"],
    ["temporary", "Temporary Role"]
  ]
}
```

### 3. User Role Assignment

#### List and Create User Role Assignments

```http
GET /core/user-roles/
POST /core/user-roles/
```

**GET Response:**

```json
{
  "user_roles": [
    {
      "id": 1,
      "user": {
        "id": 5,
        "username": "john.doe",
        "email": "john.doe@company.com"
      },
      "role": {
        "id": 2,
        "name": "Team Lead",
        "codename": "team_lead"
      },
      "department": {
        "id": 3,
        "name": "Engineering"
      },
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": null,
      "is_current": true,
      "assigned_by": "admin",
      "reason": "Promotion to team lead"
    }
  ]
}
```

**POST Request:**

```json
{
  "user_id": 5,
  "role_id": 2,
  "department_id": 3,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": null,
  "conditions": { "project_id": 15 },
  "reason": "Assigned to Project Alpha"
}
```

#### Remove User Role Assignment

```http
DELETE /core/user-roles/{user_role_id}/
```

### 4. Bulk User Registration

#### Bulk Register Users (JSON)

```http
POST /core/bulk-register/
```

**Request:**

```json
{
  "users": [
    {
      "username": "jane.smith",
      "email": "jane.smith@company.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "password": "securepassword123",
      "department_id": 2,
      "position_id": 5,
      "employee_id": "EMP001",
      "phone_number": "+1234567890",
      "supervisor_id": 10,
      "roles": [
        {
          "role_id": 3,
          "department_id": 2,
          "start_date": "2024-01-15T00:00:00Z",
          "reason": "New hire"
        }
      ]
    }
  ]
}
```

**Response:**

```json
{
  "created_users": [
    {
      "id": 15,
      "username": "jane.smith",
      "email": "jane.smith@company.com",
      "employee_id": "EMP001"
    }
  ],
  "errors": [],
  "total_created": 1,
  "total_errors": 0,
  "message": "Successfully created 1 users"
}
```

#### Bulk Register Users (CSV)

```http
POST /core/bulk-register-csv/
Content-Type: multipart/form-data
```

**CSV Format:**

```csv
username,email,first_name,last_name,password,department_id,position_id,employee_id,phone_number,supervisor_id
jane.smith,jane.smith@company.com,Jane,Smith,securepassword123,2,5,EMP001,+1234567890,10
john.doe,john.doe@company.com,John,Doe,securepassword123,3,7,EMP002,+1234567891,12
```

### 5. System Configuration

#### List and Create System Configurations

```http
GET /core/config/
POST /core/config/
```

**GET Response:**

```json
{
  "configurations": [
    {
      "key": "evaluation_period_duration",
      "value": "90",
      "description": "Duration of evaluation periods in days",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**POST Request:**

```json
{
  "key": "max_goals_per_user",
  "value": "10",
  "description": "Maximum number of goals a user can have"
}
```

#### Get and Update Specific Configuration

```http
GET /core/config/{key}/
PUT /core/config/{key}/
```

## Evaluation System APIs

### 1. Dynamic Questions Management

#### List and Create Evaluation Questions

```http
GET /evaluations/questions/
POST /evaluations/questions/
```

**GET Response:**

```json
{
  "questions": [
    {
      "id": 1,
      "question_text": "Describe your key achievements this quarter",
      "section": "responsibilities",
      "section_display": "Responsibilities",
      "staff_level": "senior",
      "staff_level_display": "Senior Staff",
      "question_type": "textarea",
      "question_type_display": "Text Area",
      "options": "",
      "required": true,
      "order": 1,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**POST Request:**

```json
{
  "question_text": "What training programs have you completed?",
  "section": "training",
  "staff_level": "junior",
  "question_type": "text",
  "options": "",
  "required": false,
  "order": 2
}
```

#### Get Question Choices

```http
GET /evaluations/questions/choices/
```

**Response:**

```json
{
  "sections": [
    ["personal_data", "Personal Data"],
    ["qualifications", "Qualifications"],
    ["training", "Training"],
    ["responsibilities", "Responsibilities"],
    ["challenges", "Challenges"],
    ["goals", "Goals"]
  ],
  "staff_levels": [
    ["junior", "Junior Staff"],
    ["senior", "Senior Staff"]
  ],
  "question_types": [
    ["text", "Text"],
    ["textarea", "Text Area"],
    ["select", "Select"],
    ["date", "Date"],
    ["number", "Number"]
  ]
}
```

#### Get Questions for Specific User

```http
GET /evaluations/questions/user/{user_id}/
```

**Response:**

```json
{
  "user": {
    "id": 5,
    "username": "john.doe",
    "email": "john.doe@company.com",
    "staff_level": "senior",
    "department": "Engineering"
  },
  "questions_by_section": {
    "Responsibilities": [
      {
        "id": 1,
        "question_text": "Describe your key achievements this quarter",
        "question_type": "textarea",
        "question_type_display": "Text Area",
        "options": "",
        "required": true,
        "order": 1
      }
    ],
    "Training": [
      {
        "id": 2,
        "question_text": "What training programs have you completed?",
        "question_type": "text",
        "question_type_display": "Text",
        "options": "",
        "required": false,
        "order": 1
      }
    ]
  }
}
```

### 2. Form Template Management

#### List and Create Form Templates

```http
GET /evaluations/form-templates/
POST /evaluations/form-templates/
```

**GET Response:**

```json
{
  "templates": [
    {
      "id": 1,
      "name": "Annual Review Template",
      "description": "Standard annual performance review",
      "form_type": "annual",
      "form_type_display": "Annual Review",
      "target_departments": ["Engineering", "Marketing"],
      "target_staff_levels": ["junior", "senior"],
      "kpis_count": 8,
      "approval_workflow": "Standard Approval",
      "created_by": "admin",
      "version": 1,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**POST Request:**

```json
{
  "name": "Probation Review Template",
  "description": "Template for probation period reviews",
  "form_type": "probation",
  "target_departments": [1, 2],
  "target_staff_levels": ["junior"],
  "kpis": [
    {
      "kpi_id": 5,
      "weight": 1.5,
      "is_required": true
    }
  ],
  "approval_workflow": 2
}
```

#### Clone Form Template

```http
POST /evaluations/form-templates/{template_id}/clone/
```

**Request:**

```json
{
  "name": "Annual Review Template v2"
}
```

#### Get Appropriate Template for User

```http
GET /evaluations/form-templates/user/{user_id}/
```

### 3. KPI Management

#### List and Create KPI Templates

```http
GET /evaluations/kpis/
POST /evaluations/kpis/
```

**GET Response:**

```json
{
  "kpis": [
    {
      "id": 1,
      "name": "Project Completion Rate",
      "description": "Percentage of projects completed on time",
      "kpi_type": "percentage",
      "kpi_type_display": "Percentage",
      "visibility": "department",
      "visibility_display": "Department Specific",
      "unit_of_measure": "%",
      "min_value": 0.0,
      "max_value": 100.0,
      "default_weight": 1.0,
      "is_auto_calculated": true,
      "data_source": "project_management",
      "target_departments": ["Engineering"],
      "created_by": "admin",
      "version": 1,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**POST Request:**

```json
{
  "name": "Customer Satisfaction Score",
  "description": "Average customer satisfaction rating",
  "kpi_type": "quantitative",
  "visibility": "all",
  "unit_of_measure": "score",
  "min_value": 1.0,
  "max_value": 5.0,
  "default_weight": 1.2,
  "is_auto_calculated": false,
  "data_source": "",
  "calculation_formula": "",
  "target_departments": [1, 2, 3]
}
```

#### Get KPI Choices

```http
GET /evaluations/kpis/choices/
```

**Response:**

```json
{
  "kpi_types": [
    ["quantitative", "Quantitative"],
    ["qualitative", "Qualitative"],
    ["percentage", "Percentage"],
    ["currency", "Currency"],
    ["boolean", "Yes/No"]
  ],
  "visibility_choices": [
    ["all", "All Staff"],
    ["management", "Management Only"],
    ["hr", "HR Only"],
    ["department", "Department Specific"],
    ["role", "Role Specific"]
  ]
}
```

### 4. Evaluation Period Management

#### List and Create Evaluation Periods

```http
GET /evaluations/periods/
POST /evaluations/periods/
```

**GET Response:**

```json
{
  "periods": [
    {
      "id": 1,
      "name": "Q1 2024 Performance Review",
      "start_date": "2024-01-01",
      "end_date": "2024-03-31",
      "submission_deadline": "2024-03-15T23:59:59Z",
      "is_active": true,
      "is_open_for_submission": true,
      "description": "First quarter performance review period",
      "evaluations_count": 45,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**POST Request:**

```json
{
  "name": "Q2 2024 Performance Review",
  "start_date": "2024-04-01",
  "end_date": "2024-06-30",
  "submission_deadline": "2024-06-15T23:59:59Z",
  "is_open_for_submission": false,
  "description": "Second quarter performance review period"
}
```

### 5. Conditional Approval Rules

#### List and Create Conditional Approval Rules

```http
GET /evaluations/approval-rules/
POST /evaluations/approval-rules/
```

**GET Response:**

```json
{
  "rules": [
    {
      "id": 1,
      "name": "Low Score Escalation",
      "description": "Escalate evaluations with scores below 50%",
      "condition_type": "score_threshold",
      "condition_type_display": "Score Threshold",
      "condition_parameters": {
        "threshold": 50
      },
      "action": "escalate",
      "action_display": "Escalate to Higher Level",
      "action_parameters": {
        "approver_id": 15,
        "approval_level_id": 3
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**POST Request:**

```json
{
  "name": "Department Specific Approval",
  "description": "Require HR approval for engineering department",
  "condition_type": "department",
  "condition_parameters": {
    "department_id": 2
  },
  "action": "add_approver",
  "action_parameters": {
    "approver_id": 10,
    "approval_level_id": 2
  }
}
```

#### Get Conditional Approval Choices

```http
GET /evaluations/approval-rules/choices/
```

**Response:**

```json
{
  "condition_types": [
    ["score_threshold", "Score Threshold"],
    ["kpi_failure", "KPI Failure"],
    ["department", "Department Specific"],
    ["role", "Role Specific"],
    ["custom", "Custom Condition"]
  ],
  "actions": [
    ["add_approver", "Add Approver"],
    ["escalate", "Escalate to Higher Level"],
    ["notify_hr", "Notify HR"],
    ["require_improvement_plan", "Require Improvement Plan"]
  ]
}
```

### 6. Analytics APIs

#### Get Period Analytics

```http
GET /evaluations/analytics/period/{period_id}/
```

**Response:**

```json
{
  "period": {
    "id": 1,
    "name": "Q1 2024 Performance Review",
    "start_date": "2024-01-01",
    "end_date": "2024-03-31"
  },
  "department": {
    "id": 2,
    "name": "Engineering"
  },
  "total_evaluations": 25,
  "completed_evaluations": 22,
  "completion_rate": 88.0,
  "average_score": 78.5,
  "top_performers_count": 8,
  "improvement_needed_count": 3,
  "kpi_trends": {
    "Project Completion Rate": 85.2,
    "Code Quality Score": 92.1,
    "Team Collaboration": 88.7
  },
  "approval_times": {
    "Level 1": 2.5,
    "Level 2": 1.8,
    "HR Review": 3.2
  }
}
```

#### Get Department Performance Comparison

```http
GET /evaluations/analytics/period/{period_id}/department-comparison/
```

**Response:**

```json
{
  "comparison": [
    {
      "department": "Engineering",
      "total_evaluations": 25,
      "completion_rate": 88.0,
      "average_score": 78.5,
      "top_performers_rate": 32.0
    },
    {
      "department": "Marketing",
      "total_evaluations": 18,
      "completion_rate": 94.4,
      "average_score": 82.1,
      "top_performers_rate": 38.9
    }
  ]
}
```

#### Get KPI Performance Trends

```http
GET /evaluations/analytics/period/{period_id}/kpi-trends/
```

**Response:**

```json
{
  "trends": [
    {
      "kpi_name": "Code Quality Score",
      "average_score": 92.1,
      "unit": "score",
      "total_responses": 25
    },
    {
      "kpi_name": "Project Completion Rate",
      "average_score": 85.2,
      "unit": "%",
      "total_responses": 25
    }
  ]
}
```

## Permission System

### Permission Checking

The system uses a granular permission system with the following structure:

```python
# Check if user has permission
has_permission(user, permission_type, resource_type, department_id=dept_id)

# Examples:
has_permission(user, 'create', 'evaluation')  # Can create evaluations
has_permission(user, 'approve', 'evaluation', department_id=2)  # Can approve evaluations in dept 2
has_permission(user, 'view_analytics', 'analytics')  # Can view analytics
```

### Role-Based Access

```python
# Check if user has role
has_role(user, 'hr', department_id=2)  # HR role in department 2
has_role(user, 'admin')  # Admin role system-wide
```

### Common Permission Checks

```python
# Utility functions
can_manage_users(user, department_id=2)
can_manage_roles(user, department_id=2)
can_approve_evaluations(user, department_id=2)
can_view_analytics(user, department_id=2)
can_configure_system(user)
is_hr_user(user)
is_admin_user(user)
is_supervisor_user(user)
```

## Error Handling

All APIs return consistent error responses:

```json
{
  "error": "Permission denied"
}
```

**HTTP Status Codes:**

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `403` - Forbidden (Permission denied)
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

APIs are rate-limited to prevent abuse:

- 100 requests per minute per user
- 1000 requests per hour per user

## Caching

Permission and role data is cached for 5 minutes to improve performance.

## Security

- All APIs require authentication
- CSRF protection enabled
- Input validation and sanitization
- SQL injection protection
- XSS protection

## Usage Examples

### Creating a Role with Permissions

```bash
curl -X POST https://apes.techonstreet.com/api/core/roles/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Team Lead",
    "codename": "team_lead",
    "description": "Team leadership role",
    "role_type": "department",
    "department_id": 2,
    "permissions": [
      {"permission_id": 5, "conditions": {"department_id": 2}},
      {"permission_id": 8, "conditions": {}}
    ]
  }'
```

### Bulk User Registration

```bash
curl -X POST https://apes.techonstreet.com/api/core/bulk-register/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {
        "username": "john.doe",
        "email": "john.doe@company.com",
        "first_name": "John",
        "last_name": "Doe",
        "department_id": 2,
        "roles": [{"role_id": 3, "department_id": 2}]
      }
    ]
  }'
```

### Getting Questions for User

```bash
curl -X GET https://apes.techonstreet.com/api/evaluations/questions/user/5/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

This comprehensive API system provides full CRUD operations for all aspects of the dynamic role-based appraisal system, with granular permissions and role-based access control.
