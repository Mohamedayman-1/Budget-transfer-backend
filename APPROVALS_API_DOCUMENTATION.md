# Approvals API Documentation

This document describes the REST API endpoints for the approval workflow system.

## Base URL
All endpoints are prefixed with: `/api/approvals/`

## Authentication
All endpoints require authentication. Include the authentication token in the request headers:
```
Authorization: Bearer <your_token>
```

## API Endpoints

### 1. Start Approval Workflow
**Endpoint:** `POST /api/approvals/start-workflow/`

**Description:** Creates and starts a complete approval workflow for a budget transfer.

**Request Body:**
```json
{
    "budget_transfer_id": 123,
    "transfer_type": "FAR"  // Optional: FAR, AFR, FAD, GEN
}
```

**Response:**
```json
{
    "success": true,
    "message": "Workflow started successfully",
    "workflow_instance": {
        "id": 456,
        "status": "in_progress",
        "template": {...},
        "current_stage_template": {...},
        "stage_instances": [...]
    }
}
```

### 2. Create Workflow Instance (Without Starting)
**Endpoint:** `POST /api/approvals/create-workflow/`

**Description:** Creates a workflow instance but doesn't activate the first stage.

**Request Body:**
```json
{
    "budget_transfer_id": 123,
    "transfer_type": "FAR"  // Optional
}
```

**Response:**
```json
{
    "success": true,
    "message": "Workflow instance created successfully",
    "workflow_instance": {...}
}
```

### 3. Process User Action
**Endpoint:** `POST /api/approvals/process-action/{budget_transfer_id}/`

**Description:** Main endpoint for users to take actions on budget transfers.

**Request Body:**
```json
{
    "action": "approve",  // approve, reject, delegate, comment
    "comment": "Approved with conditions"  // Optional
}
```

**Response:**
```json
{
    "success": true,
    "message": "Action approve processed successfully",
    "workflow_instance": {...},
    "stage_finished": true,
    "outcome": "approved"
}
```

### 4. Activate Next Stage
**Endpoint:** `POST /api/approvals/activate-next-stage/{budget_transfer_id}/`

**Description:** Manually activates the next stage in the workflow.

**Response:**
```json
{
    "success": true,
    "message": "Next stage activated successfully",
    "workflow_instance": {...}
}
```

### 5. Cancel Workflow
**Endpoint:** `POST /api/approvals/cancel-workflow/`

**Description:** Cancels an active workflow.

**Request Body:**
```json
{
    "budget_transfer_id": 123,
    "reason": "Business requirement changed"  // Optional
}
```

**Response:**
```json
{
    "success": true,
    "message": "Workflow cancelled successfully",
    "workflow_instance": {...}
}
```

### 6. Check Stage Status
**Endpoint:** `GET /api/approvals/check-stage-status/{budget_transfer_id}/`

**Description:** Checks if the current stage is finished and what the outcome is.

**Response:**
```json
{
    "budget_transfer_id": 123,
    "stage_finished": true,
    "outcome": "approved",
    "workflow_instance": {...}
}
```

### 7. Get User Pending Approvals
**Endpoint:** `GET /api/approvals/pending-approvals/`

**Description:** Returns all pending approvals for the authenticated user.

**Response:**
```json
{
    "count": 5,
    "assignments": [
        {
            "id": 789,
            "user": {...},
            "stage_instance": {...},
            "status": "pending",
            "is_mandatory": true
        }
    ],
    "budget_transfers": [
        {
            "id": 123,
            "transfer_amount": "10000.00",
            "transfer_date": "2025-08-21",
            "description": "Emergency transfer",
            "status": "pending_approval"
        }
    ]
}
```

### 8. Delegate Approval
**Endpoint:** `POST /api/approvals/delegate/`

**Description:** Delegates approval responsibility to another user.

**Request Body:**
```json
{
    "to_user_id": 456,
    "stage_instance_id": 789,
    "comment": "Delegating due to vacation"  // Optional
}
```

**Response:**
```json
{
    "success": true,
    "message": "Approval delegated to john_doe successfully",
    "delegation": {
        "id": 123,
        "from_user": {...},
        "to_user": {...},
        "stage_instance": {...},
        "active": true
    }
}
```

### 9. List Workflow Templates
**Endpoint:** `GET /api/approvals/templates/`

**Description:** Lists all active workflow templates.

**Response:**
```json
[
    {
        "id": 1,
        "code": "FAR_APPROVAL_V1",
        "transfer_type": "FAR",
        "name": "FAR Transfer Approval",
        "description": "Standard FAR transfer approval workflow",
        "is_active": true,
        "version": 1,
        "stages": [...]
    }
]
```

### 10. Get Workflow Instance Details
**Endpoint:** `GET /api/approvals/workflow-instance/{id}/`

**Description:** Returns detailed information about a specific workflow instance.

**Response:**
```json
{
    "id": 456,
    "status": "in_progress",
    "template": {...},
    "current_stage_template": {...},
    "stage_instances": [...],
    "completed_stage_count": 2,
    "created_at": "2025-08-21T10:00:00Z",
    "finished_at": null
}
```

### 11. Get Workflow by Budget Transfer
**Endpoint:** `GET /api/approvals/workflow-by-transfer/{budget_transfer_id}/`

**Description:** Returns workflow instance associated with a budget transfer.

**Response:**
```json
{
    "id": 456,
    "status": "in_progress",
    "template": {...},
    "current_stage_template": {...},
    "stage_instances": [...]
}
```

## Template and Stage Management APIs

### 12. Create Workflow Template
**Endpoint:** `POST /api/approvals/templates/create/`

**Description:** Creates a new workflow template.

**Request Body:**
```json
{
    "code": "FAR_APPROVAL_V2",
    "transfer_type": "FAR",
    "name": "FAR Transfer Approval v2",
    "description": "Updated FAR transfer approval workflow",
    "is_active": true,
    "version": 2
}
```

**Response:**
```json
{
    "success": true,
    "message": "Workflow template created successfully",
    "template": {
        "id": 123,
        "code": "FAR_APPROVAL_V2",
        "transfer_type": "FAR",
        "name": "FAR Transfer Approval v2",
        "description": "Updated FAR transfer approval workflow",
        "is_active": true,
        "version": 2,
        "stages": []
    }
}
```

### 13. Update Workflow Template
**Endpoint:** `PUT /api/approvals/templates/{id}/update/`

**Description:** Updates an existing workflow template.

**Request Body:**
```json
{
    "name": "Updated Template Name",
    "description": "Updated description",
    "is_active": false
}
```

**Response:**
```json
{
    "success": true,
    "message": "Workflow template updated successfully",
    "template": {...}
}
```

### 14. Delete Workflow Template
**Endpoint:** `DELETE /api/approvals/templates/{id}/delete/`

**Description:** Deactivates a workflow template (soft delete).

**Response:**
```json
{
    "success": true,
    "message": "Workflow template deactivated successfully"
}
```

### 15. Create Stage Template
**Endpoint:** `POST /api/approvals/templates/{template_id}/stages/create/`

**Description:** Creates a new stage template for a workflow template.

**Request Body:**
```json
{
    "order_index": 1,
    "name": "Department Head Approval",
    "decision_policy": "ALL",
    "quorum_count": null,
    "required_user_level": 2,
    "required_role": "department_head",
    "allow_reject": true,
    "allow_delegate": true,
    "sla_hours": 24,
    "parallel_group": null
}
```

**Response:**
```json
{
    "success": true,
    "message": "Stage template created successfully",
    "stage": {
        "id": 456,
        "workflow_template": 123,
        "order_index": 1,
        "name": "Department Head Approval",
        "decision_policy": "ALL",
        "required_user_level": {
            "id": 2,
            "name": "Department Head",
            "level": 2
        },
        "required_role": "department_head",
        "allow_reject": true,
        "allow_delegate": true,
        "sla_hours": 24
    }
}
```

### 16. Bulk Create Stages
**Endpoint:** `POST /api/approvals/templates/{template_id}/stages/bulk-create/`

**Description:** Creates multiple stage templates at once.

**Request Body:**
```json
{
    "stages": [
        {
            "order_index": 1,
            "name": "Department Head Approval",
            "decision_policy": "ALL",
            "required_user_level": 2,
            "required_role": "department_head",
            "allow_reject": true,
            "allow_delegate": true,
            "sla_hours": 24
        },
        {
            "order_index": 2,
            "name": "Finance Director Approval",
            "decision_policy": "ANY",
            "required_user_level": 3,
            "required_role": "finance_director",
            "allow_reject": true,
            "allow_delegate": false,
            "sla_hours": 48
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "message": "2 stages created successfully",
    "stages": [...]
}
```

### 17. Update Stage Template
**Endpoint:** `PUT /api/approvals/stages/{id}/update/`

**Description:** Updates an existing stage template.

**Request Body:**
```json
{
    "name": "Updated Stage Name",
    "decision_policy": "QUORUM",
    "quorum_count": 2,
    "sla_hours": 48
}
```

**Response:**
```json
{
    "success": true,
    "message": "Stage template updated successfully",
    "stage": {...}
}
```

### 18. Delete Stage Template
**Endpoint:** `DELETE /api/approvals/stages/{id}/delete/`

**Description:** Deletes a stage template (hard delete).

**Response:**
```json
{
    "success": true,
    "message": "Stage template deleted successfully"
}
```

### 19. Get Template Stages
**Endpoint:** `GET /api/approvals/templates/{template_id}/stages/`

**Description:** Returns all stages for a specific template.

**Response:**
```json
{
    "template": {
        "id": 123,
        "code": "FAR_APPROVAL_V2",
        "name": "FAR Transfer Approval v2"
    },
    "stages": [
        {
            "id": 456,
            "order_index": 1,
            "name": "Department Head Approval",
            "decision_policy": "ALL"
        },
        {
            "id": 457,
            "order_index": 2,
            "name": "Finance Director Approval",
            "decision_policy": "ANY"
        }
    ],
    "stage_count": 2
}
```

### 20. Reorder Stage Templates
**Endpoint:** `POST /api/approvals/templates/{template_id}/stages/reorder/`

**Description:** Reorders stages within a template.

**Request Body:**
```json
{
    "stage_ids": [457, 456, 458]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Stages reordered successfully",
    "stages": [...]
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
    "success": false,
    "message": "Error description"
}
```

Common HTTP status codes:
- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Usage Examples

### Starting a Workflow for a Budget Transfer
```python
import requests

# Start workflow
response = requests.post(
    'http://your-api/api/approvals/start-workflow/',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'budget_transfer_id': 123,
        'transfer_type': 'FAR'
    }
)

workflow_data = response.json()
print(f"Workflow started: {workflow_data['workflow_instance']['id']}")
```

### Approving a Budget Transfer
```python
# User approves a transfer
response = requests.post(
    'http://your-api/api/approvals/process-action/123/',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'action': 'approve',
        'comment': 'Looks good to me'
    }
)

result = response.json()
print(f"Stage finished: {result['stage_finished']}")
print(f"Outcome: {result['outcome']}")
```

### Getting Pending Approvals
```python
# Get user's pending approvals
response = requests.get(
    'http://your-api/api/approvals/pending-approvals/',
    headers={'Authorization': 'Bearer your_token'}
)

pending = response.json()
print(f"You have {pending['count']} pending approvals")
```

### Delegating an Approval
```python
# Delegate approval to another user
response = requests.post(
    'http://your-api/api/approvals/delegate/',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'to_user_id': 456,
        'stage_instance_id': 789,
        'comment': 'Delegating while on vacation'
    }
)

delegation = response.json()
print(f"Delegated to: {delegation['delegation']['to_user']['username']}")
```

### Creating a Complete Workflow Template
```python
# 1. Create a new workflow template
template_response = requests.post(
    'http://your-api/api/approvals/templates/create/',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'code': 'FAR_APPROVAL_V3',
        'transfer_type': 'FAR',
        'name': 'FAR Transfer Approval v3',
        'description': 'Enhanced FAR transfer approval workflow',
        'is_active': True,
        'version': 3
    }
)

template = template_response.json()['template']
template_id = template['id']

# 2. Create multiple stages for the template
stages_response = requests.post(
    f'http://your-api/api/approvals/templates/{template_id}/stages/bulk-create/',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'stages': [
            {
                'order_index': 1,
                'name': 'Department Head Review',
                'decision_policy': 'ALL',
                'required_user_level': 2,
                'required_role': 'department_head',
                'allow_reject': True,
                'allow_delegate': True,
                'sla_hours': 24
            },
            {
                'order_index': 2,
                'name': 'Finance Director Approval',
                'decision_policy': 'ANY',
                'required_user_level': 3,
                'required_role': 'finance_director',
                'allow_reject': True,
                'allow_delegate': False,
                'sla_hours': 48
            },
            {
                'order_index': 3,
                'name': 'CEO Final Approval',
                'decision_policy': 'ALL',
                'required_user_level': 4,
                'required_role': 'ceo',
                'allow_reject': True,
                'allow_delegate': False,
                'sla_hours': 72
            }
        ]
    }
)

stages = stages_response.json()['stages']
print(f"Created {len(stages)} stages for template")

# 3. Get complete template with stages
template_details = requests.get(
    f'http://your-api/api/approvals/templates/{template_id}/stages/',
    headers={'Authorization': 'Bearer your_token'}
)

complete_template = template_details.json()
print(f"Template has {complete_template['stage_count']} stages")
```

### Managing Template Stages
```python
# Create a single stage
stage_response = requests.post(
    f'http://your-api/api/approvals/templates/{template_id}/stages/create/',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'order_index': 4,
        'name': 'Compliance Review',
        'decision_policy': 'QUORUM',
        'quorum_count': 2,
        'required_role': 'compliance_officer',
        'allow_reject': True,
        'allow_delegate': True,
        'sla_hours': 24
    }
)

stage = stage_response.json()['stage']
stage_id = stage['id']

# Update the stage
update_response = requests.put(
    f'http://your-api/api/approvals/stages/{stage_id}/update/',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'name': 'Enhanced Compliance Review',
        'sla_hours': 48
    }
)

# Reorder stages (move compliance review to position 2)
reorder_response = requests.post(
    f'http://your-api/api/approvals/templates/{template_id}/stages/reorder/',
    headers={'Authorization': 'Bearer your_token'},
    json={
        'stage_ids': [456, stage_id, 457, 458]  # New order
    }
)

print("Stages reordered successfully")
```

## Integration Notes

1. **Workflow Lifecycle**: Always start with `start-workflow` endpoint for new budget transfers.
2. **User Actions**: Use `process-action` for all user interactions (approve/reject/delegate).
3. **Status Monitoring**: Use `check-stage-status` to monitor workflow progress.
4. **Pending Work**: Use `pending-approvals` to show users their pending tasks.
5. **Delegation**: Use the dedicated `delegate` endpoint for formal delegation processes.
6. **Template Management**: Use template creation APIs to set up new approval workflows.
7. **Stage Configuration**: Create stages with proper order_index and decision policies.
8. **Template Versioning**: Use version numbers to track template changes over time.

## Template Design Best Practices

1. **Order Index**: Start from 1 and increment sequentially for each stage.
2. **Decision Policies**: 
   - Use `ALL` when all assigned users must approve
   - Use `ANY` when any one user can approve
   - Use `QUORUM` when a specific number of approvals is needed
3. **User Level vs Role**: Use both for fine-grained access control.
4. **SLA Hours**: Set realistic timeframes for each approval stage.
5. **Delegation**: Enable delegation for stages where users might be unavailable.
6. **Rejection**: Allow rejection unless the stage is purely informational.

## Common Workflows

### Simple Two-Stage Approval
```
Stage 1: Department Head (ALL policy, required_role="department_head")
Stage 2: Finance Director (ANY policy, required_role="finance_director")
```

### Complex Multi-Level Approval
```
Stage 1: Supervisor Review (ALL policy, required_user_level=1)
Stage 2: Department Head (ANY policy, required_user_level=2) 
Stage 3: Finance Team (QUORUM policy, quorum_count=2, required_role="finance")
Stage 4: Executive Approval (ALL policy, required_user_level=4)
```

## Data Models Reference

The API returns data based on these key models:
- **ApprovalWorkflowInstance**: Main workflow state
- **ApprovalWorkflowStageInstance**: Individual stage state
- **ApprovalAssignment**: User assignments to stages
- **ApprovalAction**: User actions taken
- **ApprovalDelegation**: Delegation records
