# Budget Transfer API Collection

## Authentication Endpoints

### Register User
- **Method**: POST
- **URL**: {{base_url}}/api/auth/register/
- **Headers**: 
  - Content-Type: application/json
- **Body**:
```json
{
    "username": "test_user",
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "Test",
    "last_name": "User"
}
```
- **Response**: 201 Created

### Login
- **Method**: POST
- **URL**: {{base_url}}/api/auth/login/
- **Headers**: 
  - Content-Type: application/json
- **Body**:
```json
{
    "username": "test_user",
    "password": "securepassword123"
}
```
- **Response**: 200 OK
```json
{
    "access": "your_access_token",
    "refresh": "your_refresh_token",
    "user": {
        "id": 1,
        "username": "test_user",
        "email": "user@example.com",
        "role": "user"
    }
}
```

## Budget Management Endpoints

### Create Budget Transfer
- **Method**: POST
- **URL**: {{base_url}}/api/budget/transfers/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "amount": 5000,
    "from_code": "BUDGET001",
    "to_code": "BUDGET002",
    "description_x": "Budget transfer for Q3 expenses"
}
```
- **Response**: 201 Created

### List Budget Transfers
- **Method**: GET
- **URL**: {{base_url}}/api/budget/transfers/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Query Parameters**:
  - page: 1
  - page_size: 10
  - code: BUDGET001 (optional)
  - requested_by: username (optional)
- **Response**: 200 OK

### Get Budget Transfer Details
- **Method**: GET
- **URL**: {{base_url}}/api/budget/transfers/{{transfer_id}}/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 200 OK

### Approve/Reject Budget Transfer
- **Method**: PUT
- **URL**: {{base_url}}/api/budget/transfers/{{transfer_id}}/approve/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "action": "approve"  // or "reject"
}
```
- **Response**: 200 OK

## ADJD Transaction Endpoints

### Create ADJD Transaction Transfer
- **Method**: POST
- **URL**: {{base_url}}/api/adjd/transfers/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "transaction": "TRANS001",
    "amount": 2500,
    "description": "Transaction transfer description"
}
```
- **Response**: 201 Created

### List ADJD Transaction Transfers
- **Method**: POST (NOTE: Using POST to filter by transaction ID)
- **URL**: {{base_url}}/api/adjd/transfers/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "transaction": "TRANS001"
}
```
- **Response**: 200 OK

### Get ADJD Transaction Transfer Details
- **Method**: GET
- **URL**: {{base_url}}/api/adjd/transfers/{{transfer_id}}/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 200 OK

### Update ADJD Transaction Transfer
- **Method**: PUT
- **URL**: {{base_url}}/api/adjd/transfers/{{transfer_id}}/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "transaction": "TRANS001",
    "amount": 3000,
    "description": "Updated transaction transfer description"
}
```
- **Response**: 200 OK

### Delete ADJD Transaction Transfer
- **Method**: DELETE
- **URL**: {{base_url}}/api/adjd/transfers/{{transfer_id}}/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 204 No Content

## Account and Entities Endpoints

### List Accounts
- **Method**: GET
- **URL**: {{base_url}}/api/accounts-entities/accounts/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 200 OK

### Create Account
- **Method**: POST
- **URL**: {{base_url}}/api/accounts-entities/accounts/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "account": "ACCT001",
    "parent": "PARENT001",
    "alias_default": "Default Account"
}
```
- **Response**: 201 Created

### Get Account Details
- **Method**: GET
- **URL**: {{base_url}}/api/accounts-entities/accounts/{{account_id}}/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 200 OK

### Update Account
- **Method**: PUT
- **URL**: {{base_url}}/api/accounts-entities/accounts/{{account_id}}/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "account": "ACCT001",
    "parent": "PARENT002",
    "alias_default": "Updated Account Name"
}
```
- **Response**: 200 OK

### Delete Account
- **Method**: DELETE
- **URL**: {{base_url}}/api/accounts-entities/accounts/{{account_id}}/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 204 No Content

### List Entities
- **Method**: GET
- **URL**: {{base_url}}/api/accounts-entities/entities/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 200 OK

### Create Entity
- **Method**: POST
- **URL**: {{base_url}}/api/accounts-entities/entities/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "entity": "ENTITY001",
    "parent": "PARENT001",
    "alias_default": "Default Entity"
}
```
- **Response**: 201 Created

### Get Entity Details
- **Method**: GET
- **URL**: {{base_url}}/api/accounts-entities/entities/{{entity_id}}/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 200 OK

### List Pivot Funds
- **Method**: GET
- **URL**: {{base_url}}/api/accounts-entities/pivot-funds/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 200 OK

### Create Pivot Fund
- **Method**: POST
- **URL**: {{base_url}}/api/accounts-entities/pivot-funds/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "entity": 1,
    "account": 1,
    "year": 2023,
    "actual": 5000.00,
    "fund": 4000.00,
    "budget": 6000.00,
    "encumbrance": 1000.00
}
```
- **Response**: 201 Created

## User Management Endpoints

### List Users
- **Method**: GET
- **URL**: {{base_url}}/api/users/
- **Headers**: 
  - Authorization: Bearer {{access_token}}
- **Response**: 200 OK

### Update User Permissions
- **Method**: PUT
- **URL**: {{base_url}}/api/users/{{user_id}}/permissions/
- **Headers**: 
  - Content-Type: application/json
  - Authorization: Bearer {{access_token}}
- **Body**:
```json
{
    "can_transfer_budget": true
}
```
- **Response**: 200 OK

## Setting Up Environment Variables

- **base_url**: http://localhost:8000
- **access_token**: (Store your JWT token here after login)
- **refresh_token**: (Store your refresh token here after login)
