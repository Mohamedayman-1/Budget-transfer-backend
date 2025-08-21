from django.shortcuts import render, get_object_or_404
from django.db import DatabaseError, transaction
from django.utils import timezone

# DRF imports
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

# Import models from the current app
from .models import (
    ApprovalWorkflowTemplate,
    ApprovalWorkflowStageTemplate,
    ApprovalWorkflowInstance,
    ApprovalWorkflowStageInstance,
    ApprovalAssignment,
    ApprovalAction,
    ApprovalDelegation
)

# Import related models
from user_management.models import xx_User, xx_UserLevel
from budget_management.models import xx_BudgetTransfer

# Import serializers
from .serializers import (
    ApprovalWorkflowInstanceSerializer,
    ApprovalWorkflowTemplateSerializer,
    ApprovalAssignmentSerializer,
    ApprovalDelegationSerializer,
    ProcessActionRequestSerializer,
    StartWorkflowRequestSerializer,
    CreateWorkflowRequestSerializer,
    CancelWorkflowRequestSerializer,
    DelegateApprovalRequestSerializer,
    WorkflowStatusResponseSerializer,
    PendingApprovalsResponseSerializer,
    BudgetTransferBasicSerializer,
    CreateWorkflowTemplateSerializer,
    CreateStageTemplateSerializer,
    BulkCreateStagesSerializer,
    UpdateWorkflowTemplateSerializer,
    UpdateStageTemplateSerializer,
    ApprovalWorkflowStageTemplateSerializer
)

# Create your views here.
def activate_next_stage(budget_transfer):
    """
    Progresses the workflow instance for the given budget_transfer
    to the next stage or final status.

    Handles:
    - Initial stage activation
    - Completing the current stage
    - Creating/activating the next stage
    - Marking workflow approved when all stages are done
    - Auto-creating assignments for required users
    """

    workflow_instance = getattr(budget_transfer, "workflow_instance", None)
    if not workflow_instance:
        raise ValueError(f"No workflow instance found for transfer {budget_transfer.id}")

    # Prevent progressing finished workflows
    if workflow_instance.status in [
        ApprovalWorkflowInstance.STATUS_APPROVED,
        ApprovalWorkflowInstance.STATUS_REJECTED,
        ApprovalWorkflowInstance.STATUS_CANCELLED,
    ]:
        return workflow_instance

    with transaction.atomic():
        # Get current active stage (if any)

        # try:
        #     workflow_instance = (
        #         ApprovalWorkflowInstance.objects
        #         .select_for_update(nowait=True)
        #         .get(pk=workflow_instance.pk)
        #     )
        # except DatabaseError:
        #     raise ValueError("Workflow is being processed by another session. Try again later.")

        # Oracle limitation: FOR UPDATE cannot be used with LIMIT/OFFSET (which .first() adds).
        # Do a two-step: fetch the id without lock, then lock that single row.
        stage_id = (
            workflow_instance.stage_instances
            .filter(status=ApprovalWorkflowStageInstance.STATUS_ACTIVE)
            .order_by("id")
            .values_list("pk", flat=True)
            .first()
        )

        if stage_id is not None:
            try:
                active_stage = (
                    ApprovalWorkflowStageInstance.objects
                    .select_for_update(nowait=True)
                    .get(pk=stage_id)
                )
            except DatabaseError:
                raise ValueError("Active stage is locked by another session. Try again later.")
        else:
            active_stage = None


        if not active_stage:
            # No active stage yet -> create first one
            first_stage_template = (
                workflow_instance.template.stages.order_by("order_index").first()
            )
            if not first_stage_template:
                raise ValueError("Workflow template has no stages defined")

            new_stage = ApprovalWorkflowStageInstance.objects.create(
                workflow_instance=workflow_instance,
                stage_template=first_stage_template,
                status=ApprovalWorkflowStageInstance.STATUS_ACTIVE,
                activated_at=timezone.now(),
            )

            workflow_instance.current_stage_template = first_stage_template
            workflow_instance.status = ApprovalWorkflowInstance.STATUS_IN_PROGRESS
            workflow_instance.save(update_fields=["current_stage_template", "status"])

            _create_assignments(new_stage)
            return workflow_instance

        # If current stage is active, complete it
        active_stage.status = ApprovalWorkflowStageInstance.STATUS_COMPLETED
        active_stage.completed_at = timezone.now()
        active_stage.save(update_fields=["status", "completed_at"])

        workflow_instance.completed_stage_count += 1

        # Find next stage
        next_stage_template = (
            workflow_instance.template.stages
            .filter(order_index__gt=active_stage.stage_template.order_index)
            .order_by("order_index")
            .first()
        )

        if next_stage_template:
            # Create and activate the next stage
            new_stage = ApprovalWorkflowStageInstance.objects.create(
                workflow_instance=workflow_instance,
                stage_template=next_stage_template,
                status=ApprovalWorkflowStageInstance.STATUS_ACTIVE,
                activated_at=timezone.now(),
            )
            workflow_instance.current_stage_template = next_stage_template
            workflow_instance.save(
                update_fields=["current_stage_template", "completed_stage_count"]
            )
            _create_assignments(new_stage)
        else:
            # No more stages → workflow approved
            workflow_instance.status = ApprovalWorkflowInstance.STATUS_APPROVED
            workflow_instance.finished_at = timezone.now()
            workflow_instance.current_stage_template = None
            workflow_instance.save(
                update_fields=["status", "finished_at", "completed_stage_count", "current_stage_template"]
            )

    return workflow_instance
def _create_assignments(stage_instance):
    """
    Internal helper: create ApprovalAssignment records for a stage
    based on required_user_level / required_role.
    """

    stage_template = stage_instance.stage_template
    required_level = stage_template.required_user_level
    required_role = stage_template.required_role

    qs = xx_User.objects.all()
    if required_level:
        qs = qs.filter(user_level_id=required_level.id)
    if required_role:
        qs = qs.filter(role=required_role)

    for user in qs:
        ApprovalAssignment.objects.get_or_create(
            stage_instance=stage_instance,
            user=user,
            defaults={
                "role_snapshot": user.role,
                "level_snapshot": getattr(user.level.name, "name", None),
                "is_mandatory": True,
            },
        )
def check_finished_stage(budget_transfer):
    """
    Check if the current active stage (or parallel group of stages)
    has met its decision policy and can be considered finished.

    Returns:
        (bool, str) -> (is_finished, outcome)
        outcome = "approved" | "rejected" | "pending"
    """

    workflow_instance = getattr(budget_transfer, "workflow_instance", None)
    if not workflow_instance:
        raise ValueError(f"No workflow instance found for transfer {budget_transfer.id}")

    # Determine group without locking rows with LIMIT/OFFSET
    base_qs = workflow_instance.stage_instances.filter(
        status=ApprovalWorkflowStageInstance.STATUS_ACTIVE
    )

    if not base_qs.exists():
        return False, "pending"

    parallel_group = (
        base_qs.order_by("id")
        .values_list("stage_template__parallel_group", flat=True)
        .first()
    )

    if parallel_group:
        group_qs = workflow_instance.stage_instances.filter(
            status=ApprovalWorkflowStageInstance.STATUS_ACTIVE,
            stage_template__parallel_group=parallel_group,
        )
    else:
        group_qs = base_qs

    # Lock the relevant group rows without using .first() on the locked queryset
    try:
        group_stages = group_qs.select_for_update(nowait=True)
    except DatabaseError:
        # Another session is processing these rows
        return False, "pending"

    # Evaluate each stage in the group
    all_approved = True
    any_rejected = False

    for stage in group_stages:
        if stage.stage_template.allow_reject and stage.actions.filter(action=ApprovalAction.ACTION_REJECT).exists():
            any_rejected = True
            continue  # rejection overrides approvals

        assignments = stage.assignments.all()
        approved_assignments = stage.actions.filter(
            action=ApprovalAction.ACTION_APPROVE
        ).values_list("assignment_id", flat=True).distinct()
        approved_count = len(approved_assignments)

        if stage.stage_template.decision_policy == ApprovalWorkflowStageTemplate.POLICY_ALL:
            if set(approved_assignments) != set(stage.assignments.values_list("id", flat=True)):
                all_approved = False

        elif stage.stage_template.decision_policy == ApprovalWorkflowStageTemplate.POLICY_ANY:
            if approved_count == 0:
                all_approved = False

        elif stage.stage_template.decision_policy == ApprovalWorkflowStageTemplate.POLICY_QUORUM:
            quorum = stage.stage_template.quorum_count or max(1, assignments.count() // 2 + 1)
            if approved_count < quorum:
                all_approved = False

        else:
            # Default safeguard: require at least one approval
            if approved_count == 0:
                all_approved = False

    # Decision logic for group
    if any_rejected:
        return True, "rejected"

    if all_approved:
        return True, "approved"

    return False, "pending"
def process_user_action(budget_transfer, user, action, comment=None):
    """
    MAIN entry point for approval cycle.
    Called whenever a user takes an action (approve/reject/delegate/comment).
    """
    instance = budget_transfer.workflow_instance
    if not instance:
        raise ValueError("No workflow instance found")

    # 1) Record the action
    active_stage = instance.stage_instances.filter(
        status=ApprovalWorkflowStageInstance.STATUS_ACTIVE
    ).first()
    if not active_stage:
        raise ValueError("No active stage to act on")
    
    assignment = active_stage.assignments.filter(user=user).first()
    if not assignment:
        raise ValueError(f"User {user} has no assignment in this stage")
    if action not in [ApprovalAction.ACTION_APPROVE, ApprovalAction.ACTION_REJECT,
                      ApprovalAction.ACTION_DELEGATE]:
        raise ValueError(f"Invalid action: {action}")
    if not active_stage.stage_template.allow_reject and action == ApprovalAction.ACTION_REJECT:
        raise ValueError("Rejection not allowed in this stage")
    if not active_stage.stage_template.allow_delegate and action == ApprovalAction.ACTION_DELEGATE:
        raise ValueError("Delegation not allowed in this stage")
    
    # Check if user already took action (prevent duplicate actions)
    existing_action = ApprovalAction.objects.filter(
        stage_instance=active_stage,
        user=user,
        action__in=[ApprovalAction.ACTION_APPROVE, ApprovalAction.ACTION_REJECT]
    ).first()
    if existing_action and action in [ApprovalAction.ACTION_APPROVE, ApprovalAction.ACTION_REJECT]:
        raise ValueError(f"User {user} already took action: {existing_action.action}")
    
    ApprovalAction.objects.create(
        stage_instance=active_stage,
        user=user,
        assignment=assignment,
        action=action,
        comment=comment,
        triggers_stage_completion=False,  # actual completion decided below
    )
    
    # Update assignment status for approve/reject actions
    if action in [ApprovalAction.ACTION_APPROVE, ApprovalAction.ACTION_REJECT]:
        assignment.status = action  # approved/rejected
        assignment.save(update_fields=["status"])
    
    # 2) Handle delegation separately
    if action == ApprovalAction.ACTION_DELEGATE:
        # Note: This is a simplified delegation. For full delegation, use delegate_approval() function
        # which requires a target user parameter
        assignment.status = ApprovalAssignment.STATUS_DELEGATED
        assignment.save(update_fields=["status"])
        return instance

    # 3) Ask stage-level logic if it’s finished
    finished, outcome = check_finished_stage(budget_transfer)

    # 4) If finished, update workflow accordingly
    if finished:
        if outcome == "approved":
            activate_next_stage(budget_transfer)
        elif outcome == "rejected":
            instance.status = ApprovalWorkflowInstance.STATUS_REJECTED
            instance.finished_at = timezone.now()
            instance.save(update_fields=["status", "finished_at"])

    return instance
def create_workflow_instance(budget_transfer, transfer_type=None):
    """
    Creates a new ApprovalWorkflowInstance for a budget transfer.
    Automatically selects the appropriate workflow template based on transfer type.
    
    Args:
        budget_transfer: The xx_BudgetTransfer instance
        transfer_type: Optional override for transfer type selection
    
    Returns:
        ApprovalWorkflowInstance: The created workflow instance
    """
    # Determine transfer type
    if not transfer_type:
        # Try to determine from budget_transfer attributes
        transfer_type = getattr(budget_transfer, 'transfer_type', 'GEN')
        if not transfer_type:
            transfer_type = 'GEN'  # Default to Generic
    
    # Find active template for this transfer type
    template = ApprovalWorkflowTemplate.objects.filter(
        transfer_type=transfer_type,
        is_active=True
    ).order_by('-version').first()
    
    if not template:
        # Fallback to generic template
        template = ApprovalWorkflowTemplate.objects.filter(
            transfer_type='GEN',
            is_active=True
        ).order_by('-version').first()
    
    if not template:
        raise ValueError(f"No active workflow template found for transfer type: {transfer_type}")
    
    # Create workflow instance
    workflow_instance = ApprovalWorkflowInstance.objects.create(
        budget_transfer=budget_transfer,
        template=template,
        status=ApprovalWorkflowInstance.STATUS_PENDING
    )
    
    return workflow_instance
def start_approval_workflow(budget_transfer, transfer_type=None):
    """
    Complete workflow initialization: creates instance and activates first stage.
    
    Args:
        budget_transfer: The xx_BudgetTransfer instance
        transfer_type: Optional transfer type override
    
    Returns:
        ApprovalWorkflowInstance: The initialized workflow instance
    """
    # Create workflow instance if it doesn't exist
    workflow_instance = getattr(budget_transfer, 'workflow_instance', None)
    if not workflow_instance:
        workflow_instance = create_workflow_instance(budget_transfer, transfer_type)
    
    # Activate first stage
    if workflow_instance.status == ApprovalWorkflowInstance.STATUS_PENDING:
        activate_next_stage(budget_transfer)
    
    return workflow_instance
def cancel_workflow(budget_transfer, reason=None):
    """
    Cancels an active workflow and all its stages.
    
    Args:
        budget_transfer: The xx_BudgetTransfer instance
        reason: Optional cancellation reason
    
    Returns:
        ApprovalWorkflowInstance: The cancelled workflow instance
    """
    workflow_instance = getattr(budget_transfer, 'workflow_instance', None)
    if not workflow_instance:
        raise ValueError("No workflow instance found to cancel")
    
    # Prevent cancelling already finished workflows
    if workflow_instance.status in [
        ApprovalWorkflowInstance.STATUS_APPROVED,
        ApprovalWorkflowInstance.STATUS_REJECTED,
        ApprovalWorkflowInstance.STATUS_CANCELLED,
    ]:
        return workflow_instance
    
    with transaction.atomic():
        # Cancel all active stage instances
        active_stages = workflow_instance.stage_instances.filter(
            status=ApprovalWorkflowStageInstance.STATUS_ACTIVE
        )
        for stage in active_stages:
            stage.status = ApprovalWorkflowStageInstance.STATUS_CANCELLED
            stage.completed_at = timezone.now()
            stage.save(update_fields=["status", "completed_at"])
        
        # Cancel workflow instance
        workflow_instance.status = ApprovalWorkflowInstance.STATUS_CANCELLED
        workflow_instance.finished_at = timezone.now()
        workflow_instance.current_stage_template = None
        workflow_instance.save(update_fields=["status", "finished_at", "current_stage_template"])
        
        # Log cancellation action
        if active_stages.exists():
            ApprovalAction.objects.create(
                stage_instance=active_stages.first(),
                user=None,  # System action
                action=ApprovalAction.ACTION_COMMENT,
                comment=f"Workflow cancelled. Reason: {reason or 'No reason provided'}",
                triggers_stage_completion=False,
            )
    
    return workflow_instance
def get_user_pending_approvals(user):
    """
    Get all pending approval assignments for a specific user.
    
    Args:
        user: The xx_User instance
    
    Returns:
        QuerySet: ApprovalAssignment objects that are pending for this user
    """
    return ApprovalAssignment.objects.filter(
        user=user,
        status=ApprovalAssignment.STATUS_PENDING,
        stage_instance__status=ApprovalWorkflowStageInstance.STATUS_ACTIVE,
        stage_instance__workflow_instance__status=ApprovalWorkflowInstance.STATUS_IN_PROGRESS
    ).select_related(
        'stage_instance__workflow_instance__budget_transfer',
        'stage_instance__stage_template'
    )
def delegate_approval(from_user, to_user, stage_instance, comment=None):
    """
    Delegates an approval from one user to another.
    
    Args:
        from_user: The user delegating their approval
        to_user: The user receiving the delegation
        stage_instance: The ApprovalWorkflowStageInstance
        comment: Optional delegation comment
    
    Returns:
        ApprovalDelegation: The created delegation record
    """
    # Validate delegation is allowed
    if not stage_instance.stage_template.allow_delegate:
        raise ValueError("Delegation not allowed in this stage")
    
    # Check from_user has assignment
    from_assignment = stage_instance.assignments.filter(user=from_user).first()
    if not from_assignment:
        raise ValueError(f"User {from_user} has no assignment in this stage")
    
    if from_assignment.status != ApprovalAssignment.STATUS_PENDING:
        raise ValueError(f"Assignment already processed: {from_assignment.status}")
    
    # Check if to_user already has assignment or delegation
    existing_assignment = stage_instance.assignments.filter(user=to_user).first()
    existing_delegation = ApprovalDelegation.objects.filter(
        to_user=to_user,
        stage_instance=stage_instance,
        active=True
    ).first()
    
    if existing_assignment or existing_delegation:
        raise ValueError(f"User {to_user} already involved in this stage")
    
    with transaction.atomic():
        # Create delegation record
        delegation = ApprovalDelegation.objects.create(
            from_user=from_user,
            to_user=to_user,
            stage_instance=stage_instance,
            active=True
        )
        
        # Create assignment for delegate
        ApprovalAssignment.objects.create(
            stage_instance=stage_instance,
            user=to_user,
            role_snapshot=to_user.role,
            level_snapshot=getattr(to_user.level, "name", None),
            is_mandatory=from_assignment.is_mandatory,
            status=ApprovalAssignment.STATUS_PENDING
        )
        
        # Update original assignment
        from_assignment.status = ApprovalAssignment.STATUS_DELEGATED
        from_assignment.save(update_fields=["status"])
        
        # Log delegation action
        ApprovalAction.objects.create(
            stage_instance=stage_instance,
            user=from_user,
            assignment=from_assignment,
            action=ApprovalAction.ACTION_DELEGATE,
            comment=comment or f"Delegated to {to_user}",
            triggers_stage_completion=False,
        )
    
    return delegation


# =========================
# API VIEWS
# =========================

class ProcessUserActionAPIView(APIView):
    """
    API endpoint for processing user actions (approve/reject/delegate/comment)
    POST /api/approvals/process-action/{budget_transfer_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, budget_transfer_id):
        try:
            budget_transfer = get_object_or_404(xx_BudgetTransfer, id=budget_transfer_id)
            serializer = ProcessActionRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            action = serializer.validated_data['action']
            comment = serializer.validated_data.get('comment', '')
            
            # Process the action
            workflow_instance = process_user_action(
                budget_transfer=budget_transfer,
                user=request.user,
                action=action,
                comment=comment
            )
            
            # Check if stage is finished
            finished, outcome = check_finished_stage(budget_transfer)
            
            response_data = {
                'success': True,
                'message': f'Action {action} processed successfully',
                'workflow_instance': ApprovalWorkflowInstanceSerializer(workflow_instance).data,
                'stage_finished': finished,
                'outcome': outcome
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StartApprovalWorkflowAPIView(APIView):
    """
    API endpoint for starting approval workflow
    POST /api/approvals/start-workflow/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = StartWorkflowRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            budget_transfer_id = serializer.validated_data['budget_transfer_id']
            transfer_type = serializer.validated_data.get('transfer_type')
            
            budget_transfer = get_object_or_404(xx_BudgetTransfer, id=budget_transfer_id)
            
            workflow_instance = start_approval_workflow(budget_transfer, transfer_type)
            
            response_data = {
                'success': True,
                'message': 'Workflow started successfully',
                'workflow_instance': ApprovalWorkflowInstanceSerializer(workflow_instance).data
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateWorkflowInstanceAPIView(APIView):
    """
    API endpoint for creating workflow instance (without starting)
    POST /api/approvals/create-workflow/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = CreateWorkflowRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            budget_transfer_id = serializer.validated_data['budget_transfer_id']
            transfer_type = serializer.validated_data.get('transfer_type')
            
            budget_transfer = get_object_or_404(xx_BudgetTransfer, id=budget_transfer_id)
            
            workflow_instance = create_workflow_instance(budget_transfer, transfer_type)
            
            response_data = {
                'success': True,
                'message': 'Workflow instance created successfully',
                'workflow_instance': ApprovalWorkflowInstanceSerializer(workflow_instance).data
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ActivateNextStageAPIView(APIView):
    """
    API endpoint for activating next stage manually
    POST /api/approvals/activate-next-stage/{budget_transfer_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, budget_transfer_id):
        try:
            budget_transfer = get_object_or_404(xx_BudgetTransfer, id=budget_transfer_id)
            
            workflow_instance = activate_next_stage(budget_transfer)
            
            response_data = {
                'success': True,
                'message': 'Next stage activated successfully',
                'workflow_instance': ApprovalWorkflowInstanceSerializer(workflow_instance).data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CancelWorkflowAPIView(APIView):
    """
    API endpoint for cancelling workflow
    POST /api/approvals/cancel-workflow/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = CancelWorkflowRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            budget_transfer_id = serializer.validated_data['budget_transfer_id']
            reason = serializer.validated_data.get('reason')
            
            budget_transfer = get_object_or_404(xx_BudgetTransfer, id=budget_transfer_id)
            
            workflow_instance = cancel_workflow(budget_transfer, reason)
            
            response_data = {
                'success': True,
                'message': 'Workflow cancelled successfully',
                'workflow_instance': ApprovalWorkflowInstanceSerializer(workflow_instance).data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CheckFinishedStageAPIView(APIView):
    """
    API endpoint for checking if current stage is finished
    GET /api/approvals/check-stage-status/{budget_transfer_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, budget_transfer_id):
        try:
            budget_transfer = get_object_or_404(xx_BudgetTransfer, id=budget_transfer_id)
            
            finished, outcome = check_finished_stage(budget_transfer)
            
            response_data = {
                'budget_transfer_id': budget_transfer_id,
                'stage_finished': finished,
                'outcome': outcome,
                'workflow_instance': ApprovalWorkflowInstanceSerializer(
                    budget_transfer.workflow_instance
                ).data if hasattr(budget_transfer, 'workflow_instance') else None
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetUserPendingApprovalsAPIView(APIView):
    """
    API endpoint for getting user's pending approvals
    GET /api/approvals/pending-approvals/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            assignments = get_user_pending_approvals(request.user)
            
            # Get related budget transfers
            budget_transfer_ids = assignments.values_list(
                'stage_instance__workflow_instance__budget_transfer_id', flat=True
            )
            budget_transfers = xx_BudgetTransfer.objects.filter(id__in=budget_transfer_ids)
            
            response_data = {
                'count': assignments.count(),
                'assignments': ApprovalAssignmentSerializer(assignments, many=True).data,
                'budget_transfers': BudgetTransferBasicSerializer(budget_transfers, many=True).data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DelegateApprovalAPIView(APIView):
    """
    API endpoint for delegating approval to another user
    POST /api/approvals/delegate/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = DelegateApprovalRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            to_user_id = serializer.validated_data['to_user_id']
            stage_instance_id = serializer.validated_data['stage_instance_id']
            comment = serializer.validated_data.get('comment')
            
            to_user = get_object_or_404(xx_User, id=to_user_id)
            stage_instance = get_object_or_404(ApprovalWorkflowStageInstance, id=stage_instance_id)
            
            delegation = delegate_approval(
                from_user=request.user,
                to_user=to_user,
                stage_instance=stage_instance,
                comment=comment
            )
            
            response_data = {
                'success': True,
                'message': f'Approval delegated to {to_user.username} successfully',
                'delegation': ApprovalDelegationSerializer(delegation).data
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'success': False, 'message': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =========================
# LIST/DETAIL API VIEWS
# =========================

class ApprovalWorkflowTemplateListAPIView(generics.ListAPIView):
    """
    API endpoint for listing workflow templates
    GET /api/approvals/templates/
    """
    queryset = ApprovalWorkflowTemplate.objects.filter(is_active=True)
    serializer_class = ApprovalWorkflowTemplateSerializer
    permission_classes = [IsAuthenticated]

class ApprovalWorkflowInstanceDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for getting workflow instance details
    GET /api/approvals/workflow-instance/{id}/
    """
    queryset = ApprovalWorkflowInstance.objects.all()
    serializer_class = ApprovalWorkflowInstanceSerializer
    permission_classes = [IsAuthenticated]

class ApprovalWorkflowInstanceByBudgetTransferAPIView(APIView):
    """
    API endpoint for getting workflow instance by budget transfer ID
    GET /api/approvals/workflow-by-transfer/{budget_transfer_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, budget_transfer_id):
        try:
            budget_transfer = get_object_or_404(xx_BudgetTransfer, id=budget_transfer_id)
            
            if hasattr(budget_transfer, 'workflow_instance'):
                workflow_instance = budget_transfer.workflow_instance
                serializer = ApprovalWorkflowInstanceSerializer(workflow_instance)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'message': 'No workflow instance found for this budget transfer'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =========================
# TEMPLATE MANAGEMENT API VIEWS
# =========================

class CreateWorkflowTemplateAPIView(APIView):
    """
    API endpoint for creating new workflow templates
    POST /api/approvals/templates/create/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = CreateWorkflowTemplateSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            template = serializer.save()
            
            response_data = {
                'success': True,
                'message': 'Workflow template created successfully',
                'template': ApprovalWorkflowTemplateSerializer(template).data
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UpdateWorkflowTemplateAPIView(APIView):
    """
    API endpoint for updating workflow templates
    PUT /api/approvals/templates/{id}/update/
    """
    permission_classes = [IsAuthenticated]
    
    def put(self, request, pk):
        try:
            template = get_object_or_404(ApprovalWorkflowTemplate, id=pk)
            serializer = UpdateWorkflowTemplateSerializer(template, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            template = serializer.save()
            
            response_data = {
                'success': True,
                'message': 'Workflow template updated successfully',
                'template': ApprovalWorkflowTemplateSerializer(template).data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DeleteWorkflowTemplateAPIView(APIView):
    """
    API endpoint for deleting workflow templates (soft delete by setting is_active=False)
    DELETE /api/approvals/templates/{id}/delete/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            template = get_object_or_404(ApprovalWorkflowTemplate, id=pk)
            
            # Check if template has active instances
            active_instances = ApprovalWorkflowInstance.objects.filter(
                template=template,
                status__in=[
                    ApprovalWorkflowInstance.STATUS_PENDING,
                    ApprovalWorkflowInstance.STATUS_IN_PROGRESS
                ]
            )
            
            if active_instances.exists():
                return Response(
                    {
                        'success': False, 
                        'message': 'Cannot delete template with active workflow instances'
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Soft delete by setting is_active=False
            template.is_active = False
            template.save(update_fields=['is_active'])
            
            response_data = {
                'success': True,
                'message': 'Workflow template deactivated successfully'
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateStageTemplateAPIView(APIView):
    """
    API endpoint for creating new stage templates
    POST /api/approvals/templates/{template_id}/stages/create/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, template_id):
        try:
            workflow_template = get_object_or_404(ApprovalWorkflowTemplate, id=template_id)
            
            # Add workflow_template to request data
            request_data = request.data.copy()
            request_data['workflow_template'] = workflow_template.id
            
            serializer = CreateStageTemplateSerializer(data=request_data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            stage = serializer.save()
            
            response_data = {
                'success': True,
                'message': 'Stage template created successfully',
                'stage': ApprovalWorkflowStageTemplateSerializer(stage).data
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BulkCreateStagesAPIView(APIView):
    """
    API endpoint for creating multiple stages at once
    POST /api/approvals/templates/{template_id}/stages/bulk-create/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, template_id):
        try:
            workflow_template = get_object_or_404(ApprovalWorkflowTemplate, id=template_id)
            
            # Add workflow_template_id to request data
            request_data = request.data.copy()
            request_data['workflow_template_id'] = template_id
            
            serializer = BulkCreateStagesSerializer(data=request_data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            stages_data = serializer.validated_data['stages']
            created_stages = []
            
            with transaction.atomic():
                for stage_data in stages_data:
                    # Convert OrderedDict to regular dict and handle FK fields properly
                    data = dict(stage_data)
                    
                    # Handle required_user_level: extract pk if it's a model instance
                    required_user_level = data.pop('required_user_level', None)
                    if required_user_level:
                        if hasattr(required_user_level, 'pk'):
                            # It's a model instance, get the pk
                            required_user_level_id = required_user_level.pk
                        else:
                            # It's already a pk value
                            required_user_level_id = required_user_level
                    else:
                        required_user_level_id = None
                    
                    # Create stage directly without re-serializing
                    stage = ApprovalWorkflowStageTemplate.objects.create(
                        workflow_template=workflow_template,
                        order_index=data.get('order_index'),
                        name=data.get('name'),
                        decision_policy=data.get('decision_policy'),
                        quorum_count=data.get('quorum_count'),
                        required_user_level=xx_UserLevel.objects.get(id=required_user_level_id) if required_user_level_id else None,
                        required_role=data.get('required_role'),
                        dynamic_filter_json=data.get('dynamic_filter_json'),
                        allow_reject=data.get('allow_reject', True),
                        allow_delegate=data.get('allow_delegate', False),
                        sla_hours=data.get('sla_hours'),
                        parallel_group=data.get('parallel_group')
                    )
                    created_stages.append(stage)
            
            response_data = {
                'success': True,
                'message': f'{len(created_stages)} stages created successfully',
                'stages': ApprovalWorkflowStageTemplateSerializer(created_stages, many=True).data
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UpdateStageTemplateAPIView(APIView):
    """
    API endpoint for updating stage templates
    PUT /api/approvals/stages/{id}/update/
    """
    permission_classes = [IsAuthenticated]
    
    def put(self, request, pk):
        try:
            stage = get_object_or_404(ApprovalWorkflowStageTemplate, id=pk)
            serializer = UpdateStageTemplateSerializer(stage, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            stage = serializer.save()
            
            response_data = {
                'success': True,
                'message': 'Stage template updated successfully',
                'stage': ApprovalWorkflowStageTemplateSerializer(stage).data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DeleteStageTemplateAPIView(APIView):
    """
    API endpoint for deleting stage templates
    DELETE /api/approvals/stages/{id}/delete/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            stage = get_object_or_404(ApprovalWorkflowStageTemplate, id=pk)
            
            # Check if stage has active instances
            active_instances = ApprovalWorkflowStageInstance.objects.filter(
                stage_template=stage,
                status__in=[
                    ApprovalWorkflowStageInstance.STATUS_PENDING,
                    ApprovalWorkflowStageInstance.STATUS_ACTIVE
                ]
            )
            
            if active_instances.exists():
                return Response(
                    {
                        'success': False, 
                        'message': 'Cannot delete stage with active instances'
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            stage.delete()
            
            response_data = {
                'success': True,
                'message': 'Stage template deleted successfully'
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetTemplateStagesAPIView(APIView):
    """
    API endpoint for getting all stages of a template
    GET /api/approvals/templates/{template_id}/stages/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, template_id):
        try:
            workflow_template = get_object_or_404(ApprovalWorkflowTemplate, id=template_id)
            stages = workflow_template.stages.all().order_by('order_index')
            
            response_data = {
                'template': ApprovalWorkflowTemplateSerializer(workflow_template).data,
                'stages': ApprovalWorkflowStageTemplateSerializer(stages, many=True).data,
                'stage_count': stages.count()
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReorderStageTemplatesAPIView(APIView):
    """
    API endpoint for reordering stage templates
    POST /api/approvals/templates/{template_id}/stages/reorder/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, template_id):
        try:
            workflow_template = get_object_or_404(ApprovalWorkflowTemplate, id=template_id)
            
            # Expect a list of stage IDs in the new order
            stage_ids = request.data.get('stage_ids', [])
            
            if not stage_ids:
                return Response(
                    {'success': False, 'message': 'stage_ids list is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify all stages belong to this template
            stages = ApprovalWorkflowStageTemplate.objects.filter(
                workflow_template=workflow_template,
                id__in=stage_ids
            )
            
            if stages.count() != len(stage_ids):
                return Response(
                    {'success': False, 'message': 'Some stage IDs are invalid'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update order_index for each stage
            with transaction.atomic():
                for index, stage_id in enumerate(stage_ids, start=1):
                    ApprovalWorkflowStageTemplate.objects.filter(id=stage_id).update(
                        order_index=index
                    )
            
            # Get updated stages
            updated_stages = workflow_template.stages.all().order_by('order_index')
            
            response_data = {
                'success': True,
                'message': 'Stages reordered successfully',
                'stages': ApprovalWorkflowStageTemplateSerializer(updated_stages, many=True).data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Internal error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




