# Dynamic Role Request System - User-Driven Role Assignment

## 🎯 System Overview

The dynamic role request system allows users to request roles themselves, giving them control over their role assignments while maintaining proper approval workflows and security controls. This system provides transparency, accountability, and flexibility in role management.

## 🏗️ Core Components

### 1. RoleRequest Model

```python
class RoleRequest(models.Model):
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    REQUEST_TYPE_CHOICES = [
        ('new_role', 'New Role'),
        ('role_extension', 'Role Extension'),
        ('role_modification', 'Role Modification'),
        ('role_removal', 'Role Removal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='pending')

    # Request details
    reason = models.TextField()
    justification = models.TextField(blank=True)
    business_case = models.TextField(blank=True)

    # Duration for temporary roles
    requested_start_date = models.DateTimeField(default=timezone.now)
    requested_end_date = models.DateTimeField(null=True, blank=True)

    # Approval workflow
    approval_workflow = models.ForeignKey('ApprovalWorkflow', on_delete=models.SET_NULL, null=True)
    current_approval_level = models.ForeignKey('ApprovalLevel', on_delete=models.SET_NULL, null=True)
```

### 2. Enhanced Role Model

```python
class Role(models.Model):
    # New fields for requestable roles
    is_requestable = models.BooleanField(default=True)  # Can users request this role?
    requires_approval = models.BooleanField(default=True)  # Does this role require approval?
    approval_workflow = models.ForeignKey('ApprovalWorkflow', on_delete=models.SET_NULL, null=True)
    max_duration_days = models.PositiveIntegerField(null=True, blank=True)  # Max duration for temporary roles
```

### 3. RoleRequestApproval Model

```python
class RoleRequestApproval(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    role_request = models.ForeignKey(RoleRequest, on_delete=models.CASCADE)
    approval_level = models.ForeignKey('ApprovalLevel', on_delete=models.CASCADE)
    approver = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
```

### 4. RoleRequestComment Model

```python
class RoleRequestComment(models.Model):
    role_request = models.ForeignKey(RoleRequest, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal comments not visible to requester
```

## 🔄 Complete User Journey

### 1. User Discovers Available Roles

```
User visits "Available Roles" page
↓
Views roles they can request (filtered by department, type)
↓
Clicks "Request Role" button
```

### 2. User Submits Role Request

```
User fills out role request form
↓
Provides reason, justification, business case
↓
Sets duration (if temporary role)
↓
Submits request
↓
System validates request
↓
If no approval required: Auto-approve and assign role
If approval required: Create approval workflow
```

### 3. Approval Workflow

```
Request goes to first approval level
↓
Approver reviews request
↓
Approver can approve, reject, or add comments
↓
If approved and more levels: Move to next level
If approved and final level: Grant role
If rejected: End workflow
```

### 4. User Tracks Request

```
User can view their request status
↓
User can add comments
↓
User can cancel pending requests
↓
User receives notifications on status changes
```

## 🎨 User Interface Features

### 1. Available Roles Page

```html
<!-- Show roles user can request -->
{% for role in available_roles %}
<div class="role-card">
  <h3>{{ role.name }}</h3>
  <p>{{ role.description }}</p>
  <div class="role-details">
    <span>Type: {{ role.get_role_type_display }}</span>
    <span
      >Department: {{ role.department.name|default:"All Departments" }}</span
    >
    <span>Approval Required: {{ role.requires_approval|yesno:"Yes,No" }}</span>
  </div>
  <a href="{% url 'request_role' %}?role={{ role.id }}" class="btn btn-primary">
    Request Role
  </a>
</div>
{% endfor %}
```

### 2. Role Request Form

```html
<form method="post" action="{% url 'request_role' %}">
  {% csrf_token %}

  <!-- Role Selection -->
  <div class="form-group">
    <label>Select Role</label>
    <select name="role" required>
      {% for role in available_roles %}
      <option value="{{ role.id }}">{{ role.name }}</option>
      {% endfor %}
    </select>
  </div>

  <!-- Request Type -->
  <div class="form-group">
    <label>Request Type</label>
    <select name="request_type" required>
      <option value="new_role">New Role</option>
      <option value="role_extension">Role Extension</option>
      <option value="role_modification">Role Modification</option>
      <option value="role_removal">Role Removal</option>
    </select>
  </div>

  <!-- Reason -->
  <div class="form-group">
    <label>Reason for Request</label>
    <textarea name="reason" required></textarea>
  </div>

  <!-- Justification -->
  <div class="form-group">
    <label>Justification</label>
    <textarea name="justification"></textarea>
  </div>

  <!-- Business Case -->
  <div class="form-group">
    <label>Business Case</label>
    <textarea name="business_case"></textarea>
  </div>

  <!-- Duration -->
  <div class="form-group">
    <label>Start Date</label>
    <input type="datetime-local" name="requested_start_date" />
  </div>

  <div class="form-group">
    <label>End Date (for temporary roles)</label>
    <input type="datetime-local" name="requested_end_date" />
  </div>

  <button type="submit" class="btn btn-primary">Submit Request</button>
</form>
```

### 3. My Role Requests Page

```html
<!-- User's role requests -->
{% for request in role_requests %}
<div class="request-card">
  <div class="request-header">
    <h4>{{ request.role.name }}</h4>
    <span class="status-badge status-{{ request.status }}">
      {{ request.get_status_display }}
    </span>
  </div>

  <div class="request-details">
    <p><strong>Type:</strong> {{ request.get_request_type_display }}</p>
    <p><strong>Reason:</strong> {{ request.reason }}</p>
    <p><strong>Submitted:</strong> {{ request.submitted_at|date }}</p>
  </div>

  <div class="request-actions">
    <a href="{% url 'role_request_detail' request.id %}" class="btn btn-info">
      View Details
    </a>

    {% if request.status == 'pending' or request.status == 'under_review' %}
    <a
      href="{% url 'cancel_role_request' request.id %}"
      class="btn btn-warning"
    >
      Cancel Request
    </a>
    {% endif %}
  </div>
</div>
{% endfor %}
```

### 4. Role Request Detail Page

```html
<!-- Request details -->
<div class="request-detail">
  <h2>Role Request: {{ role_request.role.name }}</h2>

  <div class="request-info">
    <p><strong>Status:</strong> {{ role_request.get_status_display }}</p>
    <p><strong>Type:</strong> {{ role_request.get_request_type_display }}</p>
    <p><strong>Reason:</strong> {{ role_request.reason }}</p>
    <p><strong>Justification:</strong> {{ role_request.justification }}</p>
    <p><strong>Business Case:</strong> {{ role_request.business_case }}</p>
  </div>

  <!-- Approval History -->
  <div class="approval-history">
    <h3>Approval History</h3>
    {% for approval in approvals %}
    <div class="approval-item">
      <span class="level">Level {{ approval.approval_level.level }}</span>
      <span class="status status-{{ approval.status }}">
        {{ approval.get_status_display }}
      </span>
      <span class="approver">{{ approval.approver.username }}</span>
      <span class="date">{{ approval.approved_at|date }}</span>
      {% if approval.comments %}
      <p class="comments">{{ approval.comments }}</p>
      {% endif %}
    </div>
    {% endfor %}
  </div>

  <!-- Comments -->
  <div class="comments-section">
    <h3>Comments</h3>
    {% for comment in comments %}
    <div class="comment">
      <span class="user">{{ comment.user.username }}</span>
      <span class="date">{{ comment.created_at|date }}</span>
      <p>{{ comment.comment }}</p>
    </div>
    {% endfor %}

    <!-- Add comment form -->
    <form
      method="post"
      action="{% url 'add_role_request_comment' role_request.id %}"
    >
      {% csrf_token %}
      <textarea name="comment" placeholder="Add a comment..."></textarea>
      <button type="submit" class="btn btn-primary">Add Comment</button>
    </form>
  </div>
</div>
```

## 🔧 Admin Interface

### 1. Pending Role Requests

```html
<!-- Admin view of pending requests -->
{% for request in pending_requests %}
<div class="pending-request">
  <div class="request-header">
    <h4>{{ request.user.username }} - {{ request.role.name }}</h4>
    <span class="status">{{ request.get_status_display }}</span>
  </div>

  <div class="request-summary">
    <p><strong>Type:</strong> {{ request.get_request_type_display }}</p>
    <p><strong>Reason:</strong> {{ request.reason }}</p>
    <p>
      <strong>Department:</strong> {{ request.department.name|default:"N/A" }}
    </p>
    <p><strong>Submitted:</strong> {{ request.submitted_at|date }}</p>
  </div>

  <div class="actions">
    <a
      href="{% url 'approve_role_request' request.id %}"
      class="btn btn-success"
    >
      Review Request
    </a>
  </div>
</div>
{% endfor %}
```

### 2. Approval Interface

```html
<!-- Approval form -->
<form method="post" action="{% url 'approve_role_request' role_request.id %}">
  {% csrf_token %}

  <div class="request-details">
    <h3>Role Request Details</h3>
    <p><strong>User:</strong> {{ role_request.user.username }}</p>
    <p><strong>Role:</strong> {{ role_request.role.name }}</p>
    <p><strong>Reason:</strong> {{ role_request.reason }}</p>
    <p><strong>Justification:</strong> {{ role_request.justification }}</p>
    <p><strong>Business Case:</strong> {{ role_request.business_case }}</p>
  </div>

  <div class="approval-actions">
    <div class="form-group">
      <label>Decision</label>
      <select name="action" required>
        <option value="approve">Approve</option>
        <option value="reject">Reject</option>
      </select>
    </div>

    <div class="form-group">
      <label>Comments</label>
      <textarea
        name="comments"
        placeholder="Add approval comments..."
      ></textarea>
    </div>

    <button type="submit" class="btn btn-primary">Submit Decision</button>
  </div>
</form>
```

## 🔄 Approval Workflow Logic

### 1. Auto-Approval

```python
# If role doesn't require approval, auto-approve
if not role.requires_approval:
    role_request.status = 'approved'
    role_request.approved_at = timezone.now()
    role_request.save()

    # Create user role
    UserRole.objects.create(
        user=request.user,
        role=role,
        department=role_request.department,
        start_date=role_request.requested_start_date,
        end_date=role_request.requested_end_date,
        assigned_by=request.user
    )
```

### 2. Multi-Level Approval

```python
# Check if this is the final approval
if role_request.approval_workflow:
    workflow_levels = role_request.approval_workflow.approvalworkflowlevel_set.order_by('order')
    current_level_index = list(workflow_levels.values_list('approval_level__level', flat=True)).index(
        role_request.current_approval_level.level
    )

    if current_level_index < len(workflow_levels) - 1:
        # Move to next approval level
        next_level = workflow_levels[current_level_index + 1]
        role_request.current_approval_level = next_level.approval_level
        role_request.status = 'under_review'
        role_request.save()

        # Create next approval record
        RoleRequestApproval.objects.create(
            role_request=role_request,
            approval_level=next_level.approval_level,
            approver_id=next_level.approval_level.id
        )
    else:
        # Final approval - grant role
        role_request.status = 'approved'
        role_request.approved_at = timezone.now()
        role_request.approved_by = request.user
        role_request.save()

        # Create user role
        UserRole.objects.create(
            user=role_request.user,
            role=role_request.role,
            department=role_request.department,
            start_date=role_request.requested_start_date,
            end_date=role_request.requested_end_date,
            assigned_by=request.user
        )
```

## 🎯 Key Features

### 1. User Control

- ✅ Users can browse available roles
- ✅ Users can submit role requests
- ✅ Users can track request status
- ✅ Users can add comments
- ✅ Users can cancel pending requests

### 2. Flexible Approval

- ✅ Configurable approval workflows
- ✅ Multi-level approval support
- ✅ Auto-approval for simple roles
- ✅ Approval comments and reasons

### 3. Role Configuration

- ✅ Roles can be marked as requestable
- ✅ Roles can require approval or auto-approve
- ✅ Roles can have maximum duration limits
- ✅ Department-specific role visibility

### 4. Request Types

- ✅ New role requests
- ✅ Role extensions
- ✅ Role modifications
- ✅ Role removals

### 5. Comprehensive Tracking

- ✅ Request status tracking
- ✅ Approval history
- ✅ Comments and discussions
- ✅ Audit trail

## 🔒 Security Features

### 1. Validation

```python
# Check if role is requestable
if not role.is_requestable:
    messages.error(request, 'This role cannot be requested.')
    return redirect('available_roles')

# Check if user already has this role
existing_role = UserRole.objects.filter(
    user=request.user,
    role=role,
    is_active=True
).first()

if existing_role and data.get('request_type') == 'new_role':
    messages.error(request, 'You already have this role.')
    return redirect('available_roles')
```

### 2. Department Filtering

```python
# Filter available roles by user's department
user_department = request.user.profile.department if hasattr(request.user, 'profile') else None
if user_department:
    available_roles = available_roles.filter(
        Q(department=user_department) | Q(department__isnull=True)
    )
```

### 3. Permission-Based Access

```python
@PermissionDecorator.require_permission('approve', 'role')
def approve_role_request(request, request_id):
    # Only users with approve_role permission can approve requests
```

## 📊 Analytics & Reporting

### 1. Request Statistics

```python
# Role request statistics
role_request_stats = RoleRequest.objects.values('status').annotate(
    count=Count('id')
).order_by('status')

# Department-wise request distribution
dept_request_stats = RoleRequest.objects.values('department__name').annotate(
    count=Count('id')
).order_by('-count')
```

### 2. Approval Metrics

```python
# Approval time metrics
approval_times = RoleRequest.objects.filter(
    status='approved'
).annotate(
    approval_time=ExpressionWrapper(
        F('approved_at') - F('submitted_at'),
        output_field=DurationField()
    )
).aggregate(
    avg_approval_time=Avg('approval_time'),
    min_approval_time=Min('approval_time'),
    max_approval_time=Max('approval_time')
)
```

## 🚀 Benefits Achieved

### 1. User Empowerment

- Users have control over their role requests
- Transparent process with status tracking
- Ability to provide justification and business case

### 2. Administrative Efficiency

- Reduced manual role assignment workload
- Structured approval process
- Comprehensive audit trail

### 3. Compliance & Security

- Proper approval workflows
- Justification tracking
- Department-based access control

### 4. Flexibility

- Configurable approval requirements
- Multiple request types
- Temporal constraints

### 5. Transparency

- Clear request status
- Approval history
- Comments and discussions

## 🔧 Configuration

### 1. Role Setup

```python
# Create a requestable role
role = Role.objects.create(
    name="Project Manager",
    codename="project_manager",
    description="Manages project-specific operations",
    role_type="project",
    is_requestable=True,
    requires_approval=True,
    approval_workflow=workflow,
    max_duration_days=90  # 90 days maximum
)
```

### 2. Approval Workflow

```python
# Create approval workflow
workflow = ApprovalWorkflow.objects.create(name="Role Request Approval")

# Add approval levels
level1 = ApprovalLevel.objects.create(name="Supervisor", level=1)
level2 = ApprovalLevel.objects.create(name="Department Head", level=2)
level3 = ApprovalLevel.objects.create(name="HR", level=3)

ApprovalWorkflowLevel.objects.create(workflow=workflow, approval_level=level1, order=1)
ApprovalWorkflowLevel.objects.create(workflow=workflow, approval_level=level2, order=2)
ApprovalWorkflowLevel.objects.create(workflow=workflow, approval_level=level3, order=3)
```

This dynamic role request system provides a user-friendly, secure, and efficient way for users to request roles while maintaining proper controls and approval processes.
