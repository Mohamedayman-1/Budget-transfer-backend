# Model Migration Guide: From Encrypted to Decrypted Fields

## Overview

This guide helps you migrate from encrypted Django model fields to standard Django fields with proper data types.

## ⚠️ IMPORTANT WARNINGS

1. **BACKUP YOUR DATABASE** before starting this process
2. **Test on a copy** of your production database first
3. **Plan for downtime** during the migration process
4. **Have a rollback plan** ready

## Changes Made

### Field Type Changes:

| Model | Field | Old Type | New Type | Reason |
|-------|-------|----------|----------|--------|
| xx_BudgetTransfer | transaction_date | EncryptedCharField | DateField | Proper date handling |
| xx_BudgetTransfer | amount | EncryptedCharField | DecimalField(15,2) | Proper currency handling |
| xx_BudgetTransfer | requested_by | EncryptedCharField | CharField(100) | Text data |
| xx_BudgetTransfer | notes | EncryptedCharField | TextField | Long text |
| xx_BudgetTransfer | approvel_*_date | EncryptedDateTimeField | DateTimeField | Proper datetime |
| xx_TransactionTransfer | from_center | TextField | DecimalField(15,2) | Proper currency |
| xx_TransactionTransfer | to_center | TextField | DecimalField(15,2) | Proper currency |
| XX_PivotFund | actual, budget, fund, encumbrance | EncryptedCharField | DecimalField(15,2) | Proper currency |

## Migration Steps

### Step 1: Data Export (BEFORE migration)

**Run this BEFORE applying migrations:**

```bash
# Export encrypted data to JSON (while old models are still active)
python migrate_encrypted_data.py
```

This creates backup files:
- `migrated_budget_transfers.json`
- `migrated_transaction_transfers.json`
- `migrated_pivot_funds.json`

### Step 2: Apply Database Migrations

```bash
# Apply the new migrations
python manage.py migrate
```

### Step 3: Verify Data

```bash
# Check if data migrated correctly
python manage.py shell
```

```python
# In Django shell - test queries
from budget_management.models import xx_BudgetTransfer
from adjd_transaction.models import xx_TransactionTransfer

# Test basic queries
print(f"Total transfers: {xx_BudgetTransfer.objects.count()}")
print(f"Total transaction transfers: {xx_TransactionTransfer.objects.count()}")

# Test data types
transfer = xx_BudgetTransfer.objects.first()
if transfer:
    print(f"Amount type: {type(transfer.amount)} - Value: {transfer.amount}")
    print(f"Date type: {type(transfer.transaction_date)} - Value: {transfer.transaction_date}")
```

## Benefits After Migration

### 1. **Database Performance**
- Direct SQL queries possible
- Database-level constraints and indexes work properly
- Better query optimization

### 2. **Data Integrity**
- Proper foreign key constraints
- Database-level validation
- Correct data types for calculations

### 3. **Chatbot/AI Integration**
- Direct SQL access for chatbots
- Proper aggregations and calculations
- Better reporting capabilities

### 4. **Development Experience**
- No more encryption/decryption overhead
- Cleaner code
- Better debugging
- Proper Django admin interface

## Updated Dashboard Functions

The dashboard functions have been updated to work with the new decimal fields:

```python
# Old (with Decimal conversion)
from_center = Decimal(transfer.from_center) if transfer.from_center else Decimal(0)

# New (direct float conversion)
from_center = float(transfer.from_center) if transfer.from_center else 0.0
```

## Chatbot Integration

Now you can create SQL-based chatbots:

```python
def chatbot_query(question):
    if "total amount" in question.lower():
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT SUM(amount) FROM XX_BUDGET_TRANSFER_XX WHERE status = 'approved'")
        result = cursor.fetchone()[0]
        return f"Total approved amount: ${result:,.2f}"
```

## Rollback Plan

If you need to rollback:

1. **Restore database backup**
2. **Revert model changes**
3. **Re-apply old migrations**

## Testing Checklist

- [ ] All existing views work correctly
- [ ] Dashboard displays proper data
- [ ] Decimal calculations are accurate
- [ ] Date fields display correctly
- [ ] File uploads still work
- [ ] User authentication works
- [ ] API endpoints return correct data types

## Performance Improvements Expected

1. **Faster queries** - No encryption/decryption overhead
2. **Better aggregations** - Database can do SUM, AVG, etc. directly
3. **Improved indexing** - Database indexes work on actual data
4. **Reduced memory usage** - No in-memory decryption needed

## Next Steps

After successful migration:

1. **Remove encryption middleware** if no longer needed
2. **Update API serializers** to handle new data types
3. **Create database indexes** on frequently queried fields
4. **Implement chatbot** with direct SQL access
5. **Add database constraints** for data validation

## Troubleshooting

### Common Issues:

1. **Date format errors**: Check date string formats in old data
2. **Decimal conversion errors**: Handle null/empty values properly
3. **Foreign key issues**: Ensure related data exists
4. **Performance slow**: Add database indexes after migration

### Support Commands:

```bash
# Check migration status
python manage.py showmigrations

# Rollback specific migration
python manage.py migrate app_name 0006

# Create specific migration
python manage.py makemigrations app_name --name descriptive_name
```
