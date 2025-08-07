from datetime import time
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Sum
from django.db.models.functions import Cast
from django.db.models import CharField
from user_management.models import xx_notification
from budget_management.models import (
    xx_BudgetTransfer,
    xx_BudgetTransferAttachment,
    xx_BudgetTransferRejectReason,
    xx_DashboardBudgetTransfer,
)
from adjd_transaction.models import xx_TransactionTransfer
import time
import multiprocessing
from collections import defaultdict
from decimal import Decimal




def dashboard_smart():

    try:
            # import time
            # from collections import defaultdict
            # from decimal import Decimal
            start_time = time.time()

            # Get filter parameters
            filter_cost_center = None
            filter_account_code = None

            transfer_start = time.time()
            
            # Prefetch related transfers in batches
            batch_size = 2000
            approved_transfers = []
            # We need to process all transfers since we can't filter encrypted status
            # all_transfers = xx_TransactionTransfer.objects.filter(transaction.status=="approved").select_related('transaction').only(
            all_transfers = xx_TransactionTransfer.objects.filter(transaction__status="approved").only(
                'transfer_id', 'cost_center_code', 'account_code', 
                'from_center', 'to_center', 'transaction__status'
            ).iterator(chunk_size=batch_size) 

   

            # for i in range(0, all_transfers.count(), batch_size):
            for transfer in all_transfers:
            #     # batch = all_transfers[i:i+batch_size]
                #  for transfer in batch:
                    if transfer.transaction and transfer.transaction.status == "approved":
                        approved_transfers.append({
                            "cost_center_code": transfer.cost_center_code,
                            "account_code": transfer.account_code,
                            "from_center": Decimal(transfer.from_center) if transfer.from_center else Decimal(0),
                            "to_center": Decimal(transfer.to_center) if transfer.to_center else Decimal(0),
                        })
                    
                        

            print(f"Transfer processing completed in {time.time() - transfer_start:.2f}s")


            print(f"Found {len(approved_transfers)} approved transfers")

            # PHASE 3: Aggregations (single pass through approved transfers)
            agg_start = time.time()
            
            # Initialize aggregators
            by_cost_center = defaultdict(lambda: {'from': Decimal(0), 'to': Decimal(0)})
            by_account_code = defaultdict(lambda: {'from': Decimal(0), 'to': Decimal(0)})
            by_combination = defaultdict(lambda: {'from': Decimal(0), 'to': Decimal(0)})
            filtered = []

            for transfer in approved_transfers:
                cc = transfer['cost_center_code']
                ac = transfer['account_code']
                from_amt = transfer['from_center']
                to_amt = transfer['to_center']

                # Update all aggregations in one pass
                by_cost_center[cc]['from'] += from_amt
                by_cost_center[cc]['to'] += to_amt
                
                by_account_code[ac]['from'] += from_amt
                by_account_code[ac]['to'] += to_amt
                
                combo_key = (cc, ac)
                by_combination[combo_key]['from'] += from_amt
                by_combination[combo_key]['to'] += to_amt

                # Apply filters if specified
                if (not filter_cost_center or cc == filter_cost_center) and \
                   (not filter_account_code or ac == filter_account_code):
                    filtered.append(transfer)

            # Convert aggregations to response format
            cost_center_totals = [{
                'cost_center_code': k,
                'total_from_center': v['from'],
                'total_to_center': v['to']
            } for k, v in by_cost_center.items()]

            account_code_totals = [{
                'account_code': k,
                'total_from_center': v['from'],
                'total_to_center': v['to']
            } for k, v in by_account_code.items()]

            all_combinations = [{
                'cost_center_code': k[0],
                'account_code': k[1],
                'total_from_center': v['from'],
                'total_to_center': v['to']
            } for k, v in by_combination.items()]

            print(f"Aggregation completed in {time.time() - agg_start:.2f}s")
            print(f"Total processing time: {time.time() - start_time:.2f}s")

            # Prepare final response
            data={
              
                "filtered_combinations": filtered,
                "cost_center_totals": cost_center_totals,
                "account_code_totals": account_code_totals,
                "all_combinations": all_combinations,
                "applied_filters": {
                    "cost_center_code": filter_cost_center,
                    "account_code": filter_account_code,
                },
            }

            # Save or update dashboard data
            try:
                # Get or create the single dashboard record
                dashboard, created = xx_DashboardBudgetTransfer.objects.get_or_create(
                    Dashboard_id=1,  # Use single record for all dashboard data
                    defaults={'data': '{}'}  # Initialize with empty JSON
                )
                
                # Get existing data or initialize empty dict
                existing_data = dashboard.get_data() or {}
                
                # Update the 'smart' key with new data
                existing_data['smart'] = data
                
                # Save updated data back
                dashboard.set_data(existing_data)
                dashboard.save()
                
                print(f"Smart dashboard data {'created' if created else 'updated'} successfully")
                return data
                
            except Exception as save_error:
                print(f"Error saving dashboard data: {save_error}")
                return data  # Return data even if save fails

    except Exception as e:
        print(f"Error in dashboard_smart: {e}")
        return False
    

def dashboard_normal():
     
    try:
            # import time
            # from collections import defaultdict
            # from decimal import Decimal
            start_time = time.time()

            # Get filter parameters
            filter_cost_center = None
            filter_account_code = None

            # PHASE 1: Count transfers (optimized single query)
            count_start = time.time()
            transfers = xx_BudgetTransfer.objects.only(
                'code', 'status', 'status_level','request_date'
            )

            counts = {
                'total': 0,
                'far': 0, 'afr': 0, 'fad': 0,
                'approved': 0, 'rejected': 0, 'pending': 0,
                'levels': {1: 0, 2: 0, 3: 0, 4: 0},
                'request_date': []
            }

            for transfer in transfers:
                counts['total'] += 1
                
                # Count by code prefix
                if transfer.code:
                    prefix = transfer.code[:3].upper()
                    if prefix == 'FAR': counts['far'] += 1
                    elif prefix == 'AFR': counts['afr'] += 1
                    elif prefix == 'FAD': counts['fad'] += 1
                
                # Count by status
                if transfer.status == 'approved': counts['approved'] += 1
                elif transfer.status == 'rejected': counts['rejected'] += 1
                elif transfer.status == 'pending': counts['pending'] += 1
                
                # Count by status level
                if 1 <= transfer.status_level <= 4:
                    counts['levels'][transfer.status_level] += 1
                # Collect request dates for further processing
                if transfer.request_date:
                    counts['request_date'].append(transfer.request_date)

            print(f"Count phase completed in {time.time() - count_start:.2f}s")

            data={
                "total_transfers": counts['total'],
                "total_transfers_far": counts['far'],
                "total_transfers_afr": counts['afr'],
                "total_transfers_fad": counts['fad'],
                "approved_transfers": counts['approved'],
                "rejected_transfers": counts['rejected'],
                "pending_transfers": counts['pending'],
                "pending_transfers": {
                    "Level1": counts['levels'][1],
                    "Level2": counts['levels'][2],
                    "Level3": counts['levels'][3],
                    "Level4": counts['levels'][4],
                },
            }

            # Save or update dashboard data (normal version)
            try:
                # Get or create the single dashboard record
                dashboard, created = xx_DashboardBudgetTransfer.objects.get_or_create(
                    Dashboard_id=1,  # Use same record as smart dashboard
                    defaults={'data': '{}'}  # Initialize with empty JSON
                )
                
                # Get existing data or initialize empty dict
                existing_data = dashboard.get_data() or {}
                
                # Update the 'normal' key with new data
                existing_data['normal'] = data
                
                # Save updated data back
                dashboard.set_data(existing_data)
                dashboard.save()
                
                print(f"Normal dashboard data {'created' if created else 'updated'} successfully")
                return data
                
            except Exception as save_error:
                print(f"Error saving normal dashboard data: {save_error}")
                return data  # Return data even if save fails

    except Exception as e:
        print(f"Error in dashboard_normal: {e}")
        return False


def get_saved_dashboard_data(dashboard_type='smart'):
    """
    Retrieve saved dashboard data from database
    
    Args:
        dashboard_type (str): 'smart' or 'normal'
    
    Returns:
        dict: Dashboard data or None if not found
    """
    try:
        dashboard = xx_DashboardBudgetTransfer.objects.get(Dashboard_id=1)
        all_data = dashboard.get_data() or {}
        return all_data.get(dashboard_type)
    except xx_DashboardBudgetTransfer.DoesNotExist:
        print(f"No saved dashboard data found")
        return None
    except Exception as e:
        print(f"Error retrieving {dashboard_type} dashboard data: {e}")
        return None


def get_all_dashboard_data():
    """
    Retrieve all dashboard data (both smart and normal) from database
    
    Returns:
        dict: All dashboard data or None if not found
    """
    try:
        dashboard = xx_DashboardBudgetTransfer.objects.get(Dashboard_id=1)
        print("Retrieved dashboard data successfully: ")
        return dashboard.get_data() or {}
    except xx_DashboardBudgetTransfer.DoesNotExist:
        print("No saved dashboard data found")
        return {}
    except Exception as e:
        print(f"Error retrieving dashboard data: {e}")
        return {}


def refresh_dashboard_data(dashboard_type='smart'):
    """
    Refresh dashboard data by running the appropriate function and saving to database
    
    Args:
        dashboard_type (str): 'smart' or 'normal'
    
    Returns:
        dict: Updated dashboard data or False if error
    """
    if dashboard_type == 'smart':
        return dashboard_smart()
    elif dashboard_type == 'normal':
        return dashboard_normal()
    else:
        print(f"Invalid dashboard type: {dashboard_type}")
        return False