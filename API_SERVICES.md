# API Services

This document lists all API endpoints in the Budget-transfer-backend with their authentication, required headers, parameters, and typical request/response bodies.

Base URL prefix
- Local dev (default): http://localhost:8000
- All endpoints below are relative to base and start with /api/... unless noted.

Authentication
- Scheme: JWT Bearer
- Header: Authorization: Bearer <access_token>
- Content-Type: application/json for JSON calls
- Accept: application/json

Notes
- Endpoints marked Auth: Required need a valid JWT access token.
- Pagination params (when applicable): page, page_size. Some list endpoints respond with paginated results.
- File upload endpoints use multipart/form-data.


## Auth and Users (/api/auth/)

1) POST /api/auth/register/
- Auth: Not required
- Body (json): { username, password, role?, user_level? }
- Response: 201 with { data: <user>, message, token }

2) POST /api/auth/login/
- Auth: Not required
- Body (json): { username, password }
- Response: 200 with { data: <user>, message, token, refresh }

3) POST /api/auth/token-refresh/
- Auth: Not required
- Body (json): { refresh }
- Response: 200 with { access, refresh }

4) GET /api/auth/token-expired/
- Auth: Required
- Query: none
- Response: 200 if valid, 401 if expired

5) POST /api/auth/change-password/
- Auth: Required
- Body (json): { old_password, new_password }
- Response: 200 on success

6) GET /api/auth/users/
- Auth: Required (admin)
- Response: 200 with array of users (id, username, role, can_transfer_budget, user_level)

7) PUT /api/auth/users/permission/{user_id}/
- Auth: Required (admin)
- Path params: user_id (int)
- Body (json): { can_transfer_budget: boolean }
- Response: 200 with updated flag

8) PUT /api/auth/users/update/
- Auth: Required (admin)
- Query: pk=<user_id>
- Body (json): any of { username, role, can_transfer_budget }
- Response: 200 with updated user summary

9) DELETE /api/auth/users/delete/
- Auth: Required (admin)
- Query: pk=<user_id>
- Response: 200 on delete

10) PUT /api/auth/users/level/update
- Auth: Required (admin)
- Body (json): { user_id, level_order }
- Response: 200 with updated level details

User Levels
11) GET /api/auth/levels/
- Auth: Required (admin)
- Response: 200 array of levels

12) POST /api/auth/levels/create/
- Auth: Required (admin)
- Body (json): { name, level_order, description? }
- Response: 201 with created level

13) PUT /api/auth/levels/update/
- Auth: Required (admin)
- Query: pk=<level_id>
- Body (json): any of { name, level_order, description }
- Response: 200 with updated level

14) DELETE /api/auth/levels/delete/
- Auth: Required (admin)
- Query: pk=<level_id>
- Response: 200 on delete


## Accounts and Entities (/api/accounts-entities/)

Accounts
1) GET /api/accounts-entities/accounts/
- Auth: Required
- Response: 200 with { message, data: [Account] }

2) POST /api/accounts-entities/accounts/create/
- Auth: Required
- Body (json): Account fields (see serializers)
- Response: 201 with { message, data: Account }

3) GET /api/accounts-entities/accounts/{pk}/
- Auth: Required
- Path: pk (int)
- Response: 200 with { message, data: Account }

4) PUT /api/accounts-entities/accounts/{pk}/update/
- Auth: Required
- Body (json): Account fields to update
- Response: 200 with updated data

5) DELETE /api/accounts-entities/accounts/{pk}/delete/
- Auth: Required
- Response: 200 on delete

Entities
6) GET /api/accounts-entities/entities/
- Auth: Required
- Response: 200 with { message, data: [Entity] }

7) POST /api/accounts-entities/entities/create/
- Auth: Required
- Body (json): Entity fields
- Response: 201 with { message, data: Entity }

8) GET /api/accounts-entities/entities/{pk}/
- Auth: Required
- Response: 200 with { message, data: Entity }

9) PUT /api/accounts-entities/entities/{pk}/update/
- Auth: Required
- Body (json): Entity fields to update
- Response: 200 with updated data

10) DELETE /api/accounts-entities/entities/{pk}/delete/
- Auth: Required
- Response: 200 on delete

Pivot Funds
11) GET /api/accounts-entities/pivot-funds/
- Auth: Required
- Query optional: entity, account, year
- Response: 200 paginated list

12) POST /api/accounts-entities/pivot-funds/create/
- Auth: Required
- Body (json): single object or array of objects with pivot fund fields
- Response: 201 (single) or 207 (partial) with created/errors details

13) GET /api/accounts-entities/pivot-funds/getdetail/
- Auth: Required
- Query: entity_id, account_id
- Response: 200 with details (or message if not found)

14) PUT /api/accounts-entities/pivot-funds/{pk}/update/
- Auth: Required
- Body (json): pivot fund fields to update
- Response: 200 with updated data

15) DELETE /api/accounts-entities/pivot-funds/{pk}/delete/
- Auth: Required
- Response: 200 on delete

Transaction Audits
16) GET /api/accounts-entities/transaction-audits/
- Auth: Required
- Response: 200 paginated list

17) POST /api/accounts-entities/transaction-audits/create/
- Auth: Required
- Body (json): audit fields
- Response: 201 with created record

18) GET /api/accounts-entities/transaction-audits/{pk}/
- Auth: Required
- Response: 200 with audit

19) PUT /api/accounts-entities/transaction-audits/{pk}/update/
- Auth: Required
- Body (json): fields
- Response: 200 updated

20) DELETE /api/accounts-entities/transaction-audits/{pk}/delete/
- Auth: Required
- Response: 200 on delete

Account Entity Limit
21) GET /api/accounts-entities/account-entity-limit/list/
- Auth: Required
- Query: cost_center=<entity_id> required, account_id optional
- Response: 200 paginated list of simplified records

22) POST /api/accounts-entities/account-entity-limit/upload/
- Auth: Required
- Either multipart/form-data with file=<Excel> for bulk, or application/json single record
- Response: 201/207 with created counts or errors

23) PUT /api/accounts-entities/account-entity-limit/update/
- Auth: Required
- Query: pk=<limit_id>
- Body (json): fields to update
- Response: 200 updated

24) DELETE /api/accounts-entities/account-entity-limit/delete/
- Auth: Required
- Note: View expects path param pk but URL currently lacks it. Implementation detail may need alignment.


## Budget Management (/api/budget/)

Transfers
1) POST /api/budget/transfers/create/
- Auth: Required
- Body (json): { transaction_date, notes, type: FAR|AFR|FAD, ... }
- Response: 201 with created transfer and generated code

2) POST /api/budget/transfers/list/
- Auth: Required
- Body (json): optional filters { code, date, start_date, end_date }
- Pagination: yes
- Response: 200 paginated list

3) GET /api/budget/transfers/list_underapprovel/
- Auth: Required
- Query optional: code (defaults to FAR)
- Response: 200 paginated list of transfers at current user level

4) GET /api/budget/transfers/{transfer_id}/
- Auth: Required
- Response: 200 summary of transfer

5) PUT /api/budget/transfers/{transfer_id}/update/
- Auth: Required
- Body (json): allowed fields { notes, description_x, amount, transaction_date } and include "transaction" matching the transfer id
- Response: 200 with updated transfer

6) PUT /api/budget/transfers/{transfer_id}/approve/
- Auth: Required (admin)
- Body (json): { action: "approve" | "reject" }
- Response: 200 with updated status

7) DELETE /api/budget/transfers/{transfer_id}/delete/
- Auth: Required
- Response: 200 on delete (only for pending status)

ADJD Approval/Reject Batch
8) POST /api/budget/transfers/adjd-approve-reject/
- Auth: Required
- Body: application/json; accepts list or single object. Expected structure resembles arrays within values, e.g. [{ "transaction_id": ["<id>"], "decide": [2|3], "reason": ["text"] }]
- Response: 200 with per-transaction results

Files
9) POST /api/budget/transfers/upload-files/
- Auth: Required
- Content-Type: multipart/form-data
- Fields: transaction_id, and one or more files
- Response: 201 with uploaded file metadata

10) GET /api/budget/transfers/list-files/
- Auth: Required
- Query: transaction_id
- Response: 200 with attachments including base64 file_data

11) DELETE /api/budget/transfers/{transfer_id}/attachments/{attachment_id}/
- Auth: Required
- Response: 200 on delete

Reject reasons
12) GET /api/budget/transfers/list_reject/
- Auth: Required
- Query: transaction_id
- Response: 200 with reasons list

Dashboard
13) GET /api/budget/dashboard/
- Auth: Required
- Query: type=smart|normal|all (default smart), refresh=true|false
- Response: 200 with dashboard data or info message


## ADJD Transactions (/api/adjd-transfers/)

1) GET /api/adjd-transfers/
- Auth: Required
- Query: transaction=<transaction_id> (required)
- Response: 200 with { summary, transfers, status }

2) POST /api/adjd-transfers/create/
- Auth: Required
- Body (json): single object or array. Fields include: transaction, cost_center_code, account_code, from_center, to_center, approved_budget, available_budget, encumbrance, actual, transfer_id?
- Behavior: deletes existing transfers for transaction then inserts new
- Response: 201 (single) or 207 (batch) or 400 on validation error

3) GET /api/adjd-transfers/{pk}/
- Auth: Required
- Response: 200 with transfer by primary key

4) PUT /api/adjd-transfers/{pk}/update/
- Auth: Required
- Body (json): transfer fields to update
- Response: 200 updated data

5) DELETE /api/adjd-transfers/{pk}/delete/
- Auth: Required
- Response: 204 on delete

6) POST /api/adjd-transfers/submit/
- Auth: Required
- Body (json): { transaction: <id> }
- Response: 200 submission result and pivot updates

7) POST /api/adjd-transfers/reopen/
- Auth: Required
- Body (json): { transaction: <id>, action: "reopen" }
- Response: 200 on success

8) POST /api/adjd-transfers/excel-upload/
- Auth: Required
- Content-Type: multipart/form-data
- Fields: file=<.xls/.xlsx>, transaction=<id>
- Response: 201/207/400 depending on rows processed


## Admin Panel (/api/admin_panel/)

Main Currencies
1) GET /api/admin_panel/main-currencies/
- Auth: Required
- Response: 200 with { message, data: [Currency] }

2) POST /api/admin_panel/main-currencies/create/
- Auth: Required
- Body (json): currency fields
- Response: 201 with created

3) GET /api/admin_panel/main-currencies/{pk}/
- Auth: Required
- Response: 200 with details

4) PUT /api/admin_panel/main-currencies/{pk}/update/
- Auth: Required
- Body (json): fields to update
- Response: 200

5) DELETE /api/admin_panel/main-currencies/{pk}/delete/
- Auth: Required
- Response: 204 on delete

Main Routes Names
6) GET /api/admin_panel/main-routes/
- Auth: Required
- Response: 200 { message, data: [Route] }

7) POST /api/admin_panel/main-routes/create/
- Auth: Required
- Body (json): route fields
- Response: 201 created

8) GET /api/admin_panel/main-routes/{pk}/
- Auth: Required
- Response: 200 details

9) PUT /api/admin_panel/main-routes/{pk}/update/
- Auth: Required
- Body (json): fields to update
- Response: 200

10) DELETE /api/admin_panel/main-routes/{pk}/delete/
- Auth: Required
- Response: 204 on delete


## Standard headers
- Authorization: Bearer <access_token> (for protected routes)
- Content-Type: application/json (or multipart/form-data for uploads)
- Accept: application/json

## Error handling
- 400 Bad Request: validation errors; body often includes { message or errors }
- 401 Unauthorized: missing/invalid token
- 403 Forbidden: permission denied
- 404 Not Found: resource missing
- 207 Multi-Status: batch operations with mixed results

## Pagination
- Query params: page, page_size
- Paginated responses follow DRF style: { count, next, previous, results: [...] }

## Quick cURL examples
- Login
  curl -X POST "%BASE_URL%/api/auth/login/" -H "Content-Type: application/json" -d "{\"username\":\"user\",\"password\":\"pass\"}"
- Authenticated list transfers
  curl -X POST "%BASE_URL%/api/budget/transfers/list/" -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json" -d "{}"
- Upload ADJD Excel
  curl -X POST "%BASE_URL%/api/adjd-transfers/excel-upload/" -H "Authorization: Bearer %TOKEN%" -F "transaction=123" -F "file=@transfers.xlsx"


Appendix
- Some endpoints rely on serializer-defined fields; inspect serializers for exact shapes when integrating deeply.
- A few routes expect query params for identifiers (e.g., ?pk=...), ensure you pass them correctly.
