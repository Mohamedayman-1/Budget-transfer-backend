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
from .models import (
    xx_BudgetTransfer,
    xx_BudgetTransferAttachment,
    xx_BudgetTransferRejectReason,
)
from account_and_entitys.models import XX_PivotFund, XX_Entity, XX_Account
from adjd_transaction.models import xx_TransactionTransfer
from .serializers import BudgetTransferSerializer
from user_management.permissions import IsAdmin, CanTransferBudget
from public_funtion.update_pivot_fund import update_pivot_fund
import base64
from django.db.models.functions import Cast
from django.db.models import CharField
from collections import defaultdict
from django.db.models import Prefetch
from collections import defaultdict
from decimal import Decimal
import time
import multiprocessing
from itertools import islice
from decimal import Decimal
import multiprocessing
from collections import defaultdict
from decimal import Decimal
import time
from itertools import islice
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class TransferPagination(PageNumberPagination):
    """Pagination class for budget transfers"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CreateBudgetTransferView(APIView):
    """Create budget transfers"""

    permission_classes = [IsAuthenticated]

    def post(self, request):

        if not request.data.get("transaction_date") or not request.data.get("notes"):
            return Response(
                {
                    "message": "Transaction date and notes are required fields.",
                    "errors": {
                        "transaction_date": (
                            "This field is required."
                            if not request.data.get("transaction_date")
                            else None
                        ),
                        "notes": (
                            "This field is required."
                            if not request.data.get("notes")
                            else None
                        ),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transfer_type = request.data.get("type").upper()

        if transfer_type in ["FAR", "AFR", "FAD"]:
            prefix = f"{transfer_type}-"
        else:

            prefix = "FAR-"
            

        last_transfer = (
                xx_BudgetTransfer.objects
                .filter(code__startswith=prefix)
                .order_by("-code")
                .first()
            )

        if last_transfer and last_transfer.code:
            try:
                last_num = int(last_transfer.code.replace(prefix, ""))
                new_num = last_num + 1
            except (ValueError, AttributeError):

                new_num = 1
        else:

            new_num = 1

        new_code = f"{prefix}{new_num:04d}"

        serializer = BudgetTransferSerializer(data=request.data)

        if serializer.is_valid():

            transfer = serializer.save(
                requested_by=request.user.username,
                user_id=request.user.id,
                status="pending",
                request_date=timezone.now(),
                code=new_code,
            )
            Notification_object = xx_notification.objects.create(
                user_id=request.user.id,
                message=f"New budget transfer request created with code {new_code}",
            )
            Notification_object.save()
            return Response(
                {
                    "message": "Budget transfer request created successfully.",
                    "data": BudgetTransferSerializer(transfer).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListBudgetTransferView(APIView):
    """List budget transfers with pagination"""

    permission_classes = [IsAuthenticated]
    pagination_class = TransferPagination

    def post(self, request):
        code = request.data.get("code", None)
        date = request.data.get("date", None)
        start_date = request.data.get("start_date", None)
        end_date = request.data.get("end_date", None)
        search = request.data.get("search")

        if request.user.role == "admin":
            transfers = xx_BudgetTransfer.objects.all()
        else:
            transfers = xx_BudgetTransfer.objects.filter(user_id=request.user.id)
        if code:
            # transfers = transfers.annotate(
            #     code_str=Cast('code', output_field=CharField(max_length=10))
            # )
            transfers = transfers.filter(code__icontains=code)

        transfers = transfers.order_by("-request_date")
        paginator = self.pagination_class()
        paginated_transfers = paginator.paginate_queryset(transfers, request)
        serializer = BudgetTransferSerializer(paginated_transfers, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListBudgetTransfer_approvels_View(APIView):
    """List budget transfers with pagination"""

    permission_classes = [IsAuthenticated]
    pagination_class = TransferPagination

    def get(self, request):
        code = request.query_params.get("code", None)
        date = request.data.get("date", None)
        start_date = request.data.get("start_date", None)
        end_date = request.data.get("end_date", None)
        if code is None:
            code = "FAR"
        status_level_val = (
            request.user.user_level.level_order
            if request.user.user_level.level_order
            else 0
        )
        transfers = xx_BudgetTransfer.objects.filter(
            status_level=status_level_val, code__startswith=code
        )

        if code:
            transfers = transfers.filter(code__icontains=code)



        transfers = transfers.order_by("-request_date")
        paginator = self.pagination_class()
        paginated_transfers = paginator.paginate_queryset(transfers, request)
        serializer = BudgetTransferSerializer(paginated_transfers, many=True)

        # Create a list of dictionaries with just the fields we want
        filtered_data = []
        for item in serializer.data:
            filtered_item = {
                "transaction_id": item.get("transaction_id"),
                "amount": item.get("amount"),
                "status": item.get("status"),
                "status_level": item.get("status_level"),
                "requested_by": item.get("requested_by"),
                "request_date": item.get("request_date"),
                "code": item.get("code"),
                "transaction_date": item.get("transaction_date"),
            }
            filtered_data.append(filtered_item)

        return paginator.get_paginated_response(filtered_data)


class ApproveBudgetTransferView(APIView):
    """Approve or reject budget transfer requests (admin only)"""

    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request, transfer_id):
        try:
            transfer = xx_BudgetTransfer.objects.get(transaction_id=transfer_id)

            if transfer.status != "pending":
                return Response(
                    {"message": f"This transfer has already been {transfer.status}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            action = request.data.get("action")

            if action not in ["approve", "reject"]:
                return Response(
                    {"message": 'Invalid action. Use "approve" or "reject".'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            transfer.status = "approved" if action == "approve" else "rejected"

            current_level = transfer.status_level or 0
            next_level = current_level + 1

            if next_level <= 4:
                setattr(transfer, f"approvel_{next_level}", request.user.username)
                setattr(transfer, f"approvel_{next_level}_date", timezone.now())
                transfer.status_level = next_level

            transfer.save()

            return Response(
                {
                    "message": f"Budget transfer {transfer.status}.",
                    "data": BudgetTransferSerializer(transfer).data,
                }
            )

        except xx_BudgetTransfer.DoesNotExist:
            return Response(
                {"message": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND
            )


class GetBudgetTransferView(APIView):
    """Get a specific budget transfer by ID"""

    permission_classes = [IsAuthenticated]

    def get(self, request, transfer_id):
        try:
            transfer = xx_BudgetTransfer.objects.get(transaction_id=transfer_id)

            # Check permissions: admin can see all, users can only see their own
            # if request.user.role != 'admin' and transfer.user_id != request.user.id:
            #     return Response(
            #         {'message': 'You do not have permission to view this transfer.'},
            #         status=status.HTTP_403_FORBIDDEN
            #     )
            # serializer = BudgetTransferSerializer(transfer)
            # return Response(serializer.data)
            data = {
                "transaction_id": transfer.transaction_id,
                "amount": transfer.amount,
                "status": transfer.status,
                "requested_by": transfer.requested_by,
                "description": transfer.notes,
            }

            return Response(data)

        except xx_BudgetTransfer.DoesNotExist:
            return Response(
                {"message": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND
            )


class UpdateBudgetTransferView(APIView):
    """Update a budget transfer"""

    permission_classes = [IsAuthenticated]

    def put(self, request, transfer_id):

        try:

            transfer = xx_BudgetTransfer.objects.get(transaction_id=transfer_id)
             # Get transaction_id from the request
            transaction_id = request.data.get("transaction")
            transfer = xx_BudgetTransfer.objects.get(transaction_id=transaction_id)

            if transfer.status != "pending":
                return Response(
                    {
                        "message": f'Cannot upload files for transfer with status "{transfer.status}". Only pending transfers can have files uploaded.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not request.user.role == "admin" and transfer.user_id != request.user.id:

                return Response(
                    {"message": "You do not have permission to update this transfer."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if transfer.status != "pending":
                return Response(
                    {
                        "message": f'Cannot update transfer with status "{transfer.status}". Only pending transfers can be updated.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = BudgetTransferSerializer(
                transfer, data=request.data, partial=True
            )

            if serializer.is_valid():

                allowed_fields = [
                    "notes",
                    "description_x",
                    "amount",
                    "transaction_date",
                ]

                update_data = {}
                for field in allowed_fields:
                    if field in request.data:
                        update_data[field] = request.data[field]

                if not update_data:
                    return Response(
                        {"message": "No valid fields to update."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                for key, value in update_data.items():
                    setattr(transfer, key, value)

                transfer.save()

                return Response(
                    {
                        "message": "Budget transfer updated successfully.",
                        "data": BudgetTransferSerializer(transfer).data,
                    }
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except xx_BudgetTransfer.DoesNotExist:
            return Response(
                {"message": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND
            )


class DeleteBudgetTransferView(APIView):
    """Delete a specific budget transfer by ID"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, transfer_id):
        try:
            transfer = xx_BudgetTransfer.objects.get(transaction_id=transfer_id)

            if transfer.status != "pending":
                return Response(
                    {
                        "message": f'Cannot delete transfer with status "{transfer.status}". Only pending transfers can be deleted.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if request.user.role != "admin" and transfer.user_id != request.user.id:
                return Response(
                    {"message": "You do not have permission to delete this transfer."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            transfer_code = transfer.code
            transfer.delete()

            return Response(
                {"message": f"Budget transfer {transfer_code} deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except xx_BudgetTransfer.DoesNotExist:
            return Response(
                {"message": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND
            )


class Adjdtranscationtransferapprovel_reject(APIView):
    """Submit ADJD transaction transfers for approval"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if we received valid data
        if not request.data:
            return Response(
                {
                    "error": "Empty data provided",
                    "message": "Please provide at least one transaction ID",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Convert single item to list for consistent handling
        items_to_process = []
        if isinstance(request.data, list):
            items_to_process = request.data
        else:
            # Handle single transaction case
            items_to_process = [request.data]
        results = []
        # Process each transaction
        for item in items_to_process:
            transaction_id = item.get("transaction_id")[0]
            decide = item.get("decide")[0]
            if item.get("reason") is not None:
                reson = item.get("reason")[0]
            # Validate required fields
            if not transaction_id:
                return Response(
                    {
                        "error": "transaction id is required",
                        "message": "Please provide transaction id",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if decide not in [2, 3]:
                return Response(
                    {
                        "error": "Invalid decision value",
                        "message": "Decision value must be 2 (approve) or 3 (reject)",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if decide == 3 and not reson:
                return Response(
                    {
                        "error": "Reason is required for rejection",
                        "message": "Please provide a reason for rejection",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                # Get the transfer record - use get() for single record
                trasncation = xx_BudgetTransfer.objects.get(
                    transaction_id=transaction_id
                )
                # Get the transfer type code
                code = trasncation.code.split("-")[0]
                # Handle approval flow based on transfer type
                if code == "FAR" or code == "AFR":
                    max_level = 4
                else:
                    max_level = 3
                # Update approval based on decision
                if decide == 2 and trasncation.status_level <= max_level:  # Approve
                    level = trasncation.status_level
                    # Set the appropriate approval fields
                    if level == 2:
                        trasncation.approvel_2 = request.user.username
                        trasncation.approvel_2_date = timezone.now()
                    elif level == 3:
                        trasncation.approvel_3 = request.user.username
                        trasncation.approvel_3_date = timezone.now()
                    elif level == 4:
                        trasncation.approvel_4 = request.user.username
                        trasncation.approvel_4_date = timezone.now()
                    if trasncation.status_level == max_level:
                        trasncation.status = "approved"
                    trasncation.status_level += 1
                elif decide == 3:  # Reject
                    # Record who rejected it at the current level
                    level = trasncation.status_level
                    if level == 2:
                        trasncation.approvel_2 = request.user.username
                        trasncation.approvel_2_date = timezone.now()
                    elif level == 3:
                        trasncation.approvel_3 = request.user.username
                        trasncation.approvel_3_date = timezone.now()
                    elif level == 4:
                        trasncation.approvel_4 = request.user.username
                        trasncation.approvel_4_date = timezone.now()
                    trasncation.status_level = -1
                    Reson_object = xx_BudgetTransferRejectReason.objects.create(
                        Transcation_id=trasncation,
                        reason_text=reson,
                        reject_by=request.user.username,
                    )
                    Reson_object.save()
                    trasncation.status = "rejected"
                # Save changes to the transfer
                trasncation.save()
                # Update pivot fund if final approval or rejection
                pivot_updates = []
                if (
                    max_level == trasncation.status_level and decide == 2
                ) or decide == 3:
                    trasfers = xx_TransactionTransfer.objects.filter(
                        transaction_id=transaction_id
                    )
                    for transfer in trasfers:
                        try:
                            # Extract the necessary data
                            item_cost_center = transfer.cost_center_code
                            item_account_code = transfer.account_code
                            from_center = transfer.from_center or 0
                            to_center = transfer.to_center or 0
                            # Update the pivot fund
                            update_result = update_pivot_fund(
                                item_cost_center,
                                item_account_code,
                                from_center,
                                to_center,
                                decide,
                            )
                            if update_result:
                                pivot_updates.append(update_result)
                        except Exception as e:
                            return Response(
                                {
                                    "error": "Error updating pivot fund",
                                    "message": str(e),
                                },
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            )
                        # Add the result for this transaction
                        results.append(
                            {
                                "transaction_id": transaction_id,
                                "status": "approved" if decide == 2 else "rejected",
                                "status_level": trasncation.status_level,
                                "pivot_updates": pivot_updates,
                            }
                        )
            except xx_BudgetTransfer.DoesNotExist:
                results.append(
                    {
                        "transaction_id": transaction_id,
                        "status": "error",
                        "message": f"Budget transfer not found",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "transaction_id": transaction_id,
                        "status": "error",
                        "message": str(e),
                    }
                )

        # Return all results
        return Response(
            {"message": "Transfers processed", "results": results},
            status=status.HTTP_200_OK,
        )


class BudgetTransferFileUploadView(APIView):
    """Upload files for a budget transfer and store as BLOBs"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Check if the transfer exists
            transaction_id = request.data.get("transaction_id")
            transfer = xx_BudgetTransfer.objects.get(transaction_id=transaction_id)
            if transfer.status != "pending":
                return Response(
                    {
                        "message": f'Cannot upload files for transfer with status "{transfer.status}". Only pending transfers can have files uploaded.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if any files were provided
            if not request.FILES:
                return Response(
                    {
                        "error": "No files provided",
                        "message": "Please upload at least one file",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Process each uploaded file
            uploaded_files = []
            for file_key, uploaded_file in request.FILES.items():
                # Read the file data
                file_data = uploaded_file.read()

                # Create the attachment record
                attachment = xx_BudgetTransferAttachment.objects.create(
                    budget_transfer=transfer,
                    file_name=uploaded_file.name,
                    file_type=uploaded_file.content_type,
                    file_size=len(file_data),
                    file_data=file_data,
                )

                uploaded_files.append(
                    {
                        "attachment_id": attachment.attachment_id,
                        "file_name": attachment.file_name,
                        "file_type": attachment.file_type,
                        "file_size": attachment.file_size,
                        "upload_date": attachment.upload_date,
                    }
                )

            # Update the attachment flag on the budget transfer
            transfer.attachment = "Yes"
            transfer.save()

            return Response(
                {
                    "message": f"{len(uploaded_files)} files uploaded successfully",
                    "files": uploaded_files,
                },
                status=status.HTTP_201_CREATED,
            )

        except xx_BudgetTransfer.DoesNotExist:
            return Response(
                {
                    "error": "Budget transfer not found",
                    "message": f"No budget transfer found with ID: {transaction_id}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class DeleteBudgetTransferAttachmentView(APIView):
    """Delete a specific file attachment from a budget transfer"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, transfer_id, attachment_id):
        try:
            # First, check if the budget transfer exists
            transfer = xx_BudgetTransfer.objects.get(transaction_id=transfer_id)
            if transfer.status != "pending":
                return Response(
                    {
                        "message": f'Cannot upload files for transfer with status "{transfer.status}". Only pending transfers can have files uploaded.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if user has permission to modify this transfer
            if not request.user.role == "admin" and transfer.user_id != request.user.id:
                return Response(
                    {
                        "message": "You do not have permission to modify attachments for this transfer."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Check if transfer is in editable state
            if transfer.status != "pending":
                return Response(
                    {
                        "message": f'Cannot modify attachments for transfer with status "{transfer.status}". Only pending transfers can be modified.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Find the specific attachment
            try:
                attachment = xx_BudgetTransferAttachment.objects.get(
                    attachment_id=attachment_id, budget_transfer=transfer
                )

                # Keep attachment details for response
                attachment_details = {
                    "attachment_id": attachment.attachment_id,
                    "file_name": attachment.file_name,
                }

                # Delete the attachment
                attachment.delete()

                # Check if this was the last attachment for this transfer
                remaining_attachments = xx_BudgetTransferAttachment.objects.filter(
                    budget_transfer=transfer
                ).exists()
                if not remaining_attachments:
                    transfer.attachment = "No"
                    transfer.save()

                return Response(
                    {
                        "message": f'File "{attachment_details["file_name"]}" deleted successfully',
                        "attachment_id": attachment_details["attachment_id"],
                    },
                    status=status.HTTP_200_OK,
                )

            except xx_BudgetTransferAttachment.DoesNotExist:
                return Response(
                    {
                        "error": "Attachment not found",
                        "message": f"No attachment found with ID {attachment_id} for this transfer",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        except xx_BudgetTransfer.DoesNotExist:
            return Response(
                {
                    "error": "Budget transfer not found",
                    "message": f"No budget transfer found with ID: {transfer_id}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class ListBudgetTransferAttachmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:

            transfer_id = request.query_params.get("transaction_id")
            # Retrieve the main budget transfer record
            transfer = xx_BudgetTransfer.objects.get(transaction_id=transfer_id)

            # Fetch related attachments
            attachments = xx_BudgetTransferAttachment.objects.filter(
                budget_transfer=transfer
            )

            # Build a simplified response
            data = []
            for attach in attachments:
                encoded_data = base64.b64encode(attach.file_data).decode("utf-8")
                data.append(
                    {
                        "attachment_id": attach.attachment_id,
                        "file_name": attach.file_name,
                        "file_type": attach.file_type,
                        "file_size": attach.file_size,
                        "file_data": encoded_data,  # base64-encoded
                        "upload_date": attach.upload_date,
                    }
                )

            return Response(
                {"transaction_id": transfer_id, "attachments": data},
                status=status.HTTP_200_OK,
            )
        except xx_BudgetTransfer.DoesNotExist:
            return Response(
                {"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND
            )


class list_budget_transfer_reject_reason(APIView):
    """List all budget transfer reject reasons"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            reasons = xx_BudgetTransferRejectReason.objects.filter(
                Transcation_id=request.query_params.get("transaction_id")
            )
            data = []
            for reason in reasons:
                data.append(
                    {
                        "transaction_id": reason.Transcation_id.transaction_id,
                        "reason_text": reason.reason_text,
                        "created_at": reason.reject_date,
                        "rejected by": reason.reject_by,
                    }
                )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )






#######multi proccsing ####################

# import multiprocessing
# from collections import defaultdict
# from decimal import Decimal
# import time
# from itertools import islice
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated

# # Top-level worker initialization function
# def init_worker():
#     """Initialize Django in each worker process"""
#     import os
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')  # REPLACE WITH YOUR SETTINGS
#     import django
#     django.setup()

# def process_transfer_batch(args):
#     """Process a batch of transfers in a worker process"""
#     transfer_ids, filter_cost_center, filter_account_code = args
#     from django.db import connection
#     from adjd_transaction.models import xx_TransactionTransfer
#     connection.connect()
    
#     DECIMAL_ZERO = Decimal(0)
#     batch_results = []
    
#     # Get transfers in this batch
#     transfers = xx_TransactionTransfer.objects.filter(
#         transfer_id__in=transfer_ids
#     ).select_related('transaction')
    
#     for transfer in transfers:
#         if transfer.transaction and transfer.transaction.status == "approved":
#             result = {
#                 "cost_center_code": transfer.cost_center_code,
#                 "account_code": transfer.account_code,
#                 "from_center": Decimal(str(transfer.from_center)) if transfer.from_center else DECIMAL_ZERO,
#                 "to_center": Decimal(str(transfer.to_center)) if transfer.to_center else DECIMAL_ZERO,
#             }
#             batch_results.append(result)
    
#     connection.close()
#     return batch_results

# class DashboardBudgetTransferView(APIView):
    """Optimized dashboard view with multiprocessing"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            start_time = time.time()

            # Get filter parameters
            filter_cost_center = request.query_params.get("cost_center_code")
            filter_account_code = request.query_params.get("account_code")

            # PHASE 1: Count transfers (single query)
            count_start = time.time()
            transfers = xx_BudgetTransfer.objects.only('code', 'status', 'status_level')
            
            counts = {
                'total': 0,
                'far': 0, 'afr': 0, 'fad': 0,
                'approved': 0, 'rejected': 0, 'pending': 0,
                'levels': {1: 0, 2: 0, 3: 0, 4: 0}
            }

            for transfer in transfers:
                counts['total'] += 1
                if transfer.code:
                    prefix = transfer.code[:3].upper()
                    if prefix == 'FAR': counts['far'] += 1
                    elif prefix == 'AFR': counts['afr'] += 1
                    elif prefix == 'FAD': counts['fad'] += 1
                
                if transfer.status == 'approved': counts['approved'] += 1
                elif transfer.status == 'rejected': counts['rejected'] += 1
                elif transfer.status == 'pending': counts['pending'] += 1
                
                if 1 <= transfer.status_level <= 4:
                    counts['levels'][transfer.status_level] += 1

            print(f"Count phase completed in {time.time() - count_start:.2f}s")

            # PHASE 2: Parallel transfer processing
            transfer_start = time.time()
            approved_transfers = []
            
            # Get all transfer IDs first (lightweight query)
            all_transfer_ids = list(xx_TransactionTransfer.objects.values_list(
                'transfer_id', flat=True
            ))
            
            # Configure multiprocessing
            batch_size = 500  # Smaller batches for better load balancing
            num_processes = min(multiprocessing.cpu_count() - 1 or 1, 4)  # Limit to 4 processes
            
            # Prepare batches
            batches = [
                (all_transfer_ids[i:i + batch_size], filter_cost_center, filter_account_code)
                for i in range(0, len(all_transfer_ids), batch_size)
            ]

            # Process in parallel
            with multiprocessing.Pool(
                processes=num_processes,
                initializer=init_worker
            ) as pool:
                for batch_result in pool.imap_unordered(
                    process_transfer_batch,
                    batches,
                    chunksize=1  # One batch per worker at a time
                ):
                    approved_transfers.extend(batch_result)

            print(f"Transfer processing completed in {time.time() - transfer_start:.2f}s")
            print(f"Found {len(approved_transfers)} approved transfers")

            # PHASE 3: Aggregations
            agg_start = time.time()
            by_cost_center = defaultdict(lambda: {'from': Decimal(0), 'to': Decimal(0)})
            by_account_code = defaultdict(lambda: {'from': Decimal(0), 'to': Decimal(0)})
            by_combination = defaultdict(lambda: {'from': Decimal(0), 'to': Decimal(0)})
            filtered = []

            for transfer in approved_transfers:
                cc = transfer['cost_center_code']
                ac = transfer['account_code']
                from_amt = transfer['from_center']
                to_amt = transfer['to_center']

                by_cost_center[cc]['from'] += from_amt
                by_cost_center[cc]['to'] += to_amt
                by_account_code[ac]['from'] += from_amt
                by_account_code[ac]['to'] += to_amt
                by_combination[(cc, ac)]['from'] += from_amt
                by_combination[(cc, ac)]['to'] += to_amt

                # Apply filters if specified
                if (not filter_cost_center or cc == filter_cost_center) and \
                   (not filter_account_code or ac == filter_account_code):
                    filtered.append(transfer)

            # Prepare response data
            response_data = {
                "total_transfers": counts['total'],
                "total_transfers_far": counts['far'],
                "total_transfers_afr": counts['afr'],
                "total_transfers_fad": counts['fad'],
                "approved_transfers": counts['approved'],
                "rejected_transfers": counts['rejected'],
                "pending_transfers": counts['pending'],
                "filtered_combinations": filtered,
                "cost_center_totals": [{
                    'cost_center_code': k,
                    'total_from_center': v['from'],
                    'total_to_center': v['to']
                } for k, v in by_cost_center.items()],
                "account_code_totals": [{
                    'account_code': k,
                    'total_from_center': v['from'],
                    'total_to_center': v['to']
                } for k, v in by_account_code.items()],
                "all_combinations": [{
                    'cost_center_code': k[0],
                    'account_code': k[1],
                    'total_from_center': v['from'],
                    'total_to_center': v['to']
                } for k, v in by_combination.items()],
                "applied_filters": {
                    "cost_center_code": filter_cost_center,
                    "account_code": filter_account_code,
                },
                "pending_transfers": {
                    "Level1": counts['levels'][1],
                    "Level2": counts['levels'][2],
                    "Level3": counts['levels'][3],
                    "Level4": counts['levels'][4],
                },
            }

            print(f"Aggregation completed in {time.time() - agg_start:.2f}s")
            print(f"Total processing time: {time.time() - start_time:.2f}s")

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )











class DashboardBudgetTransferView(APIView):
    """Optimized dashboard view for encrypted budget transfers"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # import time
            # from collections import defaultdict
            # from decimal import Decimal
            start_time = time.time()

            # Get filter parameters
            filter_cost_center = request.query_params.get("cost_center_code")
            filter_account_code = request.query_params.get("account_code")

            # PHASE 1: Count transfers (optimized single query)
            count_start = time.time()
            transfers = xx_BudgetTransfer.objects.only(
                'code', 'status', 'status_level'
            )
            
            counts = {
                'total': 0,
                'far': 0, 'afr': 0, 'fad': 0,
                'approved': 0, 'rejected': 0, 'pending': 0,
                'levels': {1: 0, 2: 0, 3: 0, 4: 0}
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

            print(f"Count phase completed in {time.time() - count_start:.2f}s")

            # PHASE 2: Process approved transfers (optimized with prefetch)
            transfer_start = time.time()
            
            # Prefetch related transfers in batches
            batch_size = 2000
            approved_transfers = []

            num_processes = multiprocessing.cpu_count() - 1 or 1
            
            
            # We need to process all transfers since we can't filter encrypted status
            all_transfers = xx_TransactionTransfer.objects.select_related('transaction').only(
                'transfer_id', 'cost_center_code', 'account_code', 
                'from_center', 'to_center', 'transaction__status'
            ).iterator(chunk_size=batch_size) 

            
            # for i in range(0, all_transfers.count(), batch_size):
            for transfer in all_transfers:
                # batch = all_transfers[i:i+batch_size]
                # for transfer in batch:
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
            return Response({
                "total_transfers": counts['total'],
                "total_transfers_far": counts['far'],
                "total_transfers_afr": counts['afr'],
                "total_transfers_fad": counts['fad'],
                "approved_transfers": counts['approved'],
                "rejected_transfers": counts['rejected'],
                "pending_transfers": counts['pending'],
                "filtered_combinations": filtered,
                "cost_center_totals": cost_center_totals,
                "account_code_totals": account_code_totals,
                "all_combinations": all_combinations,
                "applied_filters": {
                    "cost_center_code": filter_cost_center,
                    "account_code": filter_account_code,
                },
                "pending_transfers": {
                    "Level1": counts['levels'][1],
                    "Level2": counts['levels'][2],
                    "Level3": counts['levels'][3],
                    "Level4": counts['levels'][4],
                },
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



