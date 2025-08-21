# Budget Transfer Approvals API - Postman Collection

This repository contains a comprehensive Postman collection for testing the Budget Transfer Approval Workflow API.

## 📁 Files Included

- `Budget_Transfer_Approvals_API.postman_collection.json` - Complete Postman collection
- `APPROVALS_API_DOCUMENTATION.md` - Detailed API documentation

## 🚀 Quick Start

### 1. Import Collection to Postman

1. Open Postman
2. Click "Import" button
3. Select the `Budget_Transfer_Approvals_API.postman_collection.json` file
4. Click "Import"

### 2. Configure Environment Variables

The collection uses the following variables that you need to set:

- `base_url` - Your API base URL (default: `http://localhost:8000`)
- `auth_token` - Your authentication bearer token

#### Setting Variables:
1. In Postman, go to "Environments"
2. Create a new environment called "Budget Transfer API"
3. Add the following variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` |
| `auth_token` | `your_bearer_token_here` | `your_actual_token` |

### 3. Get Authentication Token

Before using the APIs, you need to authenticate:

1. Use your existing authentication endpoint to get a token
2. Copy the token to the `auth_token` variable
3. The collection is configured to automatically use Bearer token authentication

## 📚 Collection Structure

### 1. **Workflow Management** (4 requests)
- Start Approval Workflow
- Create Workflow Instance
- Cancel Workflow
- Activate Next Stage

### 2. **User Actions** (4 requests)
- Process User Action - Approve
- Process User Action - Reject
- Process User Action - Comment
- Delegate Approval

### 3. **Status & Information** (5 requests)
- Check Stage Status
- Get User Pending Approvals
- List Workflow Templates
- Get Workflow Instance Details
- Get Workflow by Budget Transfer

### 4. **Template Management** (6 requests)
- Create Workflow Template
- Update Workflow Template
- Delete Workflow Template
- Get Template Stages
- Reorder Stage Templates

### 5. **Stage Management** (5 requests)
- Create Stage Template
- Bulk Create Stages
- Create Stage - QUORUM Policy Example
- Update Stage Template
- Delete Stage Template

### 6. **Complete Workflow Examples** (2 example flows)
- Example 1: Simple FAR Workflow (5-step process)
- Example 2: Complex Multi-Level Workflow (2-step setup)

### 7. **Testing Scenarios** (3 requests)
- Rejection Scenario
- Delegation Scenario
- Cancel Workflow Scenario

## 🔧 Usage Examples

### Example 1: Create a Simple Workflow

1. **Create Template**
   ```
   POST /api/approvals/templates/create/
   Body: {
     "code": "SIMPLE_FAR_V1",
     "transfer_type": "FAR",
     "name": "Simple FAR Approval",
     "description": "Two-stage FAR approval workflow",
     "is_active": true,
     "version": 1
   }
   ```

2. **Create Stages**
   ```
   POST /api/approvals/templates/{template_id}/stages/bulk-create/
   Body: {
     "stages": [
       {
         "order_index": 1,
         "name": "Department Head Review",
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
         "decision_policy": "ALL",
         "required_user_level": 3,
         "required_role": "finance_director",
         "allow_reject": true,
         "allow_delegate": false,
         "sla_hours": 48
       }
     ]
   }
   ```

3. **Start Workflow**
   ```
   POST /api/approvals/start-workflow/
   Body: {
     "budget_transfer_id": 100,
     "transfer_type": "FAR"
   }
   ```

4. **Process Approvals**
   ```
   POST /api/approvals/process-action/100/
   Body: {
     "action": "approve",
     "comment": "Department approves this transfer"
   }
   ```

### Example 2: Check User's Pending Approvals

```
GET /api/approvals/pending-approvals/
```

### Example 3: Delegate Approval

```
POST /api/approvals/delegate/
Body: {
  "to_user_id": 456,
  "stage_instance_id": 789,
  "comment": "Delegating due to vacation"
}
```

## 📋 Decision Policies Explained

### ALL Policy
- **Description**: All assigned users must approve
- **Use Case**: Critical approvals requiring unanimous consent
- **Example**: Executive level approvals

### ANY Policy
- **Description**: Any one user can approve
- **Use Case**: Multiple people with same authority level
- **Example**: Any department head can approve routine transfers

### QUORUM Policy
- **Description**: Specific number of approvals required
- **Use Case**: Committee-based decisions
- **Example**: Finance committee requiring 3 out of 5 members
- **Note**: Must specify `quorum_count` when using this policy

## 🏗️ Transfer Types

- **FAR**: Financial Allocation Request
- **AFR**: Asset Funding Request  
- **FAD**: Financial Adjustment Directive
- **GEN**: Generic (fallback for other types)

## ⚠️ Important Notes

### Authentication
- All endpoints require Bearer token authentication
- Set your token in the `auth_token` environment variable
- Token is automatically included in all requests

### Error Handling
- All endpoints return consistent error responses
- HTTP status codes follow REST conventions
- Error messages provide detailed information

### Data Validation
- Templates require unique codes
- Stages require unique order_index per template
- QUORUM policy requires quorum_count > 0
- Active workflows prevent template/stage deletion

### Testing Tips
1. Start with simple workflows before complex ones
2. Use the "Check Stage Status" endpoint to monitor progress
3. Test all decision policies (ALL, ANY, QUORUM)
4. Test rejection and delegation scenarios
5. Verify error handling with invalid data

## 🐛 Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check your auth_token is valid and properly set
   - Ensure token is not expired

2. **400 Bad Request**
   - Verify request body format matches examples
   - Check required fields are provided
   - Validate data types and constraints

3. **404 Not Found**
   - Verify IDs exist (budget_transfer_id, template_id, stage_id)
   - Check URL paths match the collection

4. **500 Internal Server Error**
   - Check server logs for detailed error information
   - Verify database connections and migrations

### Variables Not Working?
- Ensure you have selected the correct environment
- Check variable names match exactly (case-sensitive)
- Verify variables are set in both "Initial Value" and "Current Value"

## 📞 Support

For additional help:
1. Check the detailed API documentation in `APPROVALS_API_DOCUMENTATION.md`
2. Review the source code in the `approvals` app
3. Check server logs for detailed error information

## 🔄 Collection Updates

This collection includes:
- ✅ All 20+ API endpoints
- ✅ Request/response examples
- ✅ Complete workflow scenarios
- ✅ Error testing scenarios
- ✅ Environment variables setup
- ✅ Authentication configuration

Happy testing! 🚀
