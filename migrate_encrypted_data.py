# #!/usr/bin/env python3
# """
# Data Migration Script: Decrypt encrypted fields and migrate to new unencrypted models

# This script helps migrate from encrypted fields to regular Django fields.
# Run this BEFORE applying the new migrations.

# Usage:
#     python migrate_encrypted_data.py

# IMPORTANT: 
# 1. Backup your database before running this script
# 2. Run this script with the OLD models (encrypted) still in place
# 3. After running this script, then apply the new migrations
# """

# import os
# import sys
# import django
# from decimal import Decimal
# from datetime import datetime

# # Add the project directory to Python path
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# # Setup Django environment
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_transfer.settings')
# django.setup()

# # Import models (these will be the OLD encrypted models when you run this)
# from budget_management.models import xx_BudgetTransfer, xx_BudgetTransferAttachment, xx_BudgetTransferRejectReason, xx_DashboardBudgetTransfer
# from adjd_transaction.models import xx_TransactionTransfer
# from user_management.models import xx_notification, xx_UserLevel
# from account_and_entitys.models import XX_Account, XX_Entity, XX_PivotFund, XX_ACCOUNT_ENTITY_LIMIT

# def migrate_budget_transfers():
#     """Migrate xx_BudgetTransfer encrypted data"""
#     print("Migrating Budget Transfers...")
    
#     # Create a temporary table to store decrypted data
#     from django.db import connection
#     cursor = connection.cursor()
    
#     # You'll need to create temporary tables or export/import the decrypted data
#     # This is a template - you'll need to adapt based on your encryption implementation
    
#     transfers = xx_BudgetTransfer.objects.all()
#     migrated_data = []
    
#     for transfer in transfers:
#         try:
#             # Convert encrypted fields to proper types
#             migrated_record = {
#                 'transaction_id': transfer.transaction_id,
#                 'transaction_date': datetime.strptime(transfer.transaction_date, '%Y-%m-%d').date() if transfer.transaction_date else None,
#                 'amount': Decimal(transfer.amount) if transfer.amount else Decimal('0.00'),
#                 'status': transfer.status,
#                 'requested_by': transfer.requested_by,
#                 'user_id': transfer.user_id,
#                 'request_date': transfer.request_date,
#                 'notes': transfer.notes,
#                 'code': transfer.code,
#                 'gl_posting_status': transfer.gl_posting_status,
#                 'approvel_1': transfer.approvel_1,
#                 'approvel_2': transfer.approvel_2,
#                 'approvel_3': transfer.approvel_3,
#                 'approvel_4': transfer.approvel_4,
#                 'approvel_1_date': transfer.approvel_1_date,
#                 'approvel_2_date': transfer.approvel_2_date,
#                 'approvel_3_date': transfer.approvel_3_date,
#                 'approvel_4_date': transfer.approvel_4_date,
#                 'status_level': transfer.status_level,
#                 'attachment': transfer.attachment,
#                 'fy': transfer.fy,
#                 'report': transfer.report,
#                 'type': transfer.type,
#             }
#             migrated_data.append(migrated_record)
            
#         except Exception as e:
#             print(f"Error migrating transfer {transfer.transaction_id}: {e}")
    
#     print(f"Prepared {len(migrated_data)} budget transfer records for migration")
#     return migrated_data

# def migrate_transaction_transfers():
#     """Migrate xx_TransactionTransfer encrypted data"""
#     print("Migrating Transaction Transfers...")
    
#     transfers = xx_TransactionTransfer.objects.all()
#     migrated_data = []
    
#     for transfer in transfers:
#         try:
#             migrated_record = {
#                 'transfer_id': transfer.transfer_id,
#                 'cost_center_code': transfer.cost_center_code,
#                 'account_name': transfer.account_name,
#                 'approved_budget': Decimal(transfer.approved_budget) if transfer.approved_budget else None,
#                 'available_budget': Decimal(transfer.available_budget) if transfer.available_budget else None,
#                 'from_center': Decimal(transfer.from_center) if transfer.from_center else None,
#                 'to_center': Decimal(transfer.to_center) if transfer.to_center else None,
#                 'transaction_id': transfer.transaction.transaction_id if transfer.transaction else None,
#                 'reason': transfer.reason,
#                 'account_code': transfer.account_code,
#                 'cost_center_name': transfer.cost_center_name,
#                 'done': transfer.done,
#                 'encumbrance': Decimal(transfer.encumbrance) if transfer.encumbrance else None,
#                 'actual': Decimal(transfer.actual) if transfer.actual else None,
#             }
#             migrated_data.append(migrated_record)
            
#         except Exception as e:
#             print(f"Error migrating transaction transfer {transfer.transfer_id}: {e}")
    
#     print(f"Prepared {len(migrated_data)} transaction transfer records for migration")
#     return migrated_data

# def migrate_pivot_funds():
#     """Migrate XX_PivotFund encrypted data"""
#     print("Migrating Pivot Funds...")
    
#     funds = XX_PivotFund.objects.all()
#     migrated_data = []
    
#     for fund in funds:
#         try:
#             migrated_record = {
#                 'entity': fund.entity,
#                 'account': fund.account,
#                 'year': fund.year,
#                 'actual': Decimal(fund.actual) if fund.actual else None,
#                 'fund': Decimal(fund.fund) if fund.fund else None,
#                 'budget': Decimal(fund.budget) if fund.budget else None,
#                 'encumbrance': Decimal(fund.encumbrance) if fund.encumbrance else None,
#             }
#             migrated_data.append(migrated_record)
            
#         except Exception as e:
#             print(f"Error migrating pivot fund {fund.id}: {e}")
    
#     print(f"Prepared {len(migrated_data)} pivot fund records for migration")
#     return migrated_data

# def export_to_json():
#     """Export all decrypted data to JSON files for backup and migration"""
#     import json
#     from datetime import date, datetime
    
#     # Custom JSON encoder for dates and decimals
#     class DateTimeEncoder(json.JSONEncoder):
#         def default(self, obj):
#             if isinstance(obj, (date, datetime)):
#                 return obj.isoformat()
#             elif isinstance(obj, Decimal):
#                 return str(obj)
#             return super().default(obj)
    
#     # Migrate all data
#     budget_transfers = migrate_budget_transfers()
#     transaction_transfers = migrate_transaction_transfers()
#     pivot_funds = migrate_pivot_funds()
    
#     # Export to JSON files
#     with open('migrated_budget_transfers.json', 'w') as f:
#         json.dump(budget_transfers, f, cls=DateTimeEncoder, indent=2)
    
#     with open('migrated_transaction_transfers.json', 'w') as f:
#         json.dump(transaction_transfers, f, cls=DateTimeEncoder, indent=2)
    
#     with open('migrated_pivot_funds.json', 'w') as f:
#         json.dump(pivot_funds, f, cls=DateTimeEncoder, indent=2)
    
#     print("\n=== Migration Data Exported ===")
#     print("Files created:")
#     print("- migrated_budget_transfers.json")
#     print("- migrated_transaction_transfers.json")
#     print("- migrated_pivot_funds.json")
#     print("\nNext steps:")
#     print("1. Backup your database")
#     print("2. Apply the new migrations: python manage.py makemigrations && python manage.py migrate")
#     print("3. Import the data using the JSON files if needed")

# if __name__ == "__main__":
#     print("=== Encrypted Data Migration Script ===")
#     print("This script will export your encrypted data in decrypted format")
#     print("Make sure to backup your database first!")
    
#     response = input("Continue? (y/N): ")
#     if response.lower() == 'y':
#         export_to_json()
#     else:
#         print("Migration cancelled.")
