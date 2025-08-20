from django.db import models
from django.utils import timezone
from django.conf import settings

"""Dynamic approval workflow models.

These models implement the flexible, data‑driven approval engine described in
`DYNAMIC_APPROVAL_DESIGN.md` allowing variable length workflows, per‑stage
assignment, and auditable approval history.

Phase 1: Models only (engine / services to be added separately).
"""

# Import user + related references lazily to avoid circular imports in migrations
from user_management.models import xx_User, xx_UserLevel  # noqa
from budget_management.models import xx_BudgetTransfer  # noqa


class ApprovalWorkflowTemplate(models.Model):
	"""Defines a reusable workflow template for a given transfer type.

	Only one active template per (transfer_type, version) should normally be used
	at runtime; older versions can remain for audit / legacy instances.
	"""

	TRANSFER_TYPE_CHOICES = [
		("FAR", "FAR"),
		("AFR", "AFR"),
		("FAD", "FAD"),
		("GEN", "Generic"),  # fallback / future
	]

	code = models.CharField(max_length=60, unique=True)
	transfer_type = models.CharField(max_length=10, choices=TRANSFER_TYPE_CHOICES)
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True, null=True)
	is_active = models.BooleanField(default=True)
	version = models.PositiveIntegerField(default=1)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "APPROVAL_WORKFLOW_TEMPLATE"
		ordering = ["transfer_type", "-version", "code"]
		indexes = [
			models.Index(fields=["transfer_type", "is_active"]),
		]

	def __str__(self):
		return f"WorkflowTemplate {self.code} v{self.version} ({'active' if self.is_active else 'inactive'})"



class ApprovalWorkflowStageTemplate(models.Model):
	"""Stage template belonging to a workflow template."""

	POLICY_ALL = "ALL"
	POLICY_ANY = "ANY"
	POLICY_QUORUM = "QUORUM"
	DECISION_POLICY_CHOICES = [
		(POLICY_ALL, "All must approve"),
		(POLICY_ANY, "Any one can approve"),
		(POLICY_QUORUM, "Quorum of approvals"),
	]

	workflow_template = models.ForeignKey(
		ApprovalWorkflowTemplate, related_name="stages", on_delete=models.CASCADE
	)
	order_index = models.PositiveIntegerField(help_text="1-based ordering of stages")
	name = models.CharField(max_length=120)
	decision_policy = models.CharField(
		max_length=10, choices=DECISION_POLICY_CHOICES, default=POLICY_ALL
	)
	quorum_count = models.PositiveIntegerField(null=True, blank=True)
	required_user_level = models.ForeignKey(
		xx_UserLevel,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="stage_templates",
		help_text="If set, assignments will include users with this level",
	)
	required_role = models.CharField(
		max_length=50, null=True, blank=True, help_text="Optional user.role filter"
	)
	dynamic_filter_json = models.TextField(
		null=True,
		blank=True,
		help_text="Reserved for future dynamic filtering (store JSON string)",
	)
	allow_reject = models.BooleanField(default=True)
	allow_delegate = models.BooleanField(default=False)
	sla_hours = models.PositiveIntegerField(null=True, blank=True)
	parallel_group = models.PositiveIntegerField(
		null=True,
		blank=True,
		help_text="Future use: stages in same group run in parallel",
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "APPROVAL_WORKFLOW_STAGE_TEMPLATE"
		ordering = ["workflow_template", "order_index"]
		unique_together = ("workflow_template", "order_index")

	def __str__(self):
		return f"StageTemplate {self.workflow_template.code}#{self.order_index} {self.name}"

  
class ApprovalWorkflowInstance(models.Model):
	"""Runtime instance of a workflow for a specific budget transfer."""

	STATUS_PENDING = "pending"
	STATUS_IN_PROGRESS = "in_progress"
	STATUS_APPROVED = "approved"
	STATUS_REJECTED = "rejected"
	STATUS_CANCELLED = "cancelled"
	STATUS_CHOICES = [
		(STATUS_PENDING, "Pending"),
		(STATUS_IN_PROGRESS, "In Progress"),
		(STATUS_APPROVED, "Approved"),
		(STATUS_REJECTED, "Rejected"),
		(STATUS_CANCELLED, "Cancelled"),
	]

	budget_transfer = models.OneToOneField(
		xx_BudgetTransfer,
		on_delete=models.CASCADE,
		related_name="workflow_instance",
		db_column="transaction_id",
	)
	template = models.ForeignKey(
		ApprovalWorkflowTemplate, on_delete=models.PROTECT, related_name="instances"
	)
	current_stage_template = models.ForeignKey(
		ApprovalWorkflowStageTemplate,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="active_instances",
	)
	status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING)
	started_at = models.DateTimeField(auto_now_add=True)
	finished_at = models.DateTimeField(null=True, blank=True)
	completed_stage_count = models.PositiveIntegerField(default=0)

	class Meta:
		db_table = "APPROVAL_WORKFLOW_INSTANCE"
		indexes = [
			models.Index(fields=["status", "current_stage_template"]),
		]

	def __str__(self):
		return f"WorkflowInstance for Transfer {self.budget_transfer_id} ({self.status})"


class ApprovalWorkflowStageInstance(models.Model):
	"""Concrete runtime stage tied to its template and parent instance."""

	STATUS_PENDING = "pending"
	STATUS_ACTIVE = "active"
	STATUS_COMPLETED = "completed"
	STATUS_SKIPPED = "skipped"
	STATUS_CANCELLED = "cancelled"
	STATUS_CHOICES = [
		(STATUS_PENDING, "Pending"),
		(STATUS_ACTIVE, "Active"),
		(STATUS_COMPLETED, "Completed"),
		(STATUS_SKIPPED, "Skipped"),
		(STATUS_CANCELLED, "Cancelled"),
	]

	workflow_instance = models.ForeignKey(
		ApprovalWorkflowInstance, related_name="stage_instances", on_delete=models.CASCADE
	)
	stage_template = models.ForeignKey(
		ApprovalWorkflowStageTemplate,
		related_name="stage_instances",
		on_delete=models.PROTECT,
	)
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
	activated_at = models.DateTimeField(null=True, blank=True)
	completed_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		db_table = "APPROVAL_WORKFLOW_STAGE_INSTANCE"
		ordering = ["workflow_instance", "stage_template__order_index"]
		indexes = [
			models.Index(fields=["workflow_instance", "status"]),
		]

	def __str__(self):
		return (
			f"StageInstance {self.stage_template.name} for Transfer {self.workflow_instance.budget_transfer_id}"
		)

	@property
	def is_terminal(self):
		return self.status in {self.STATUS_COMPLETED, self.STATUS_SKIPPED, self.STATUS_CANCELLED}


class ApprovalAssignment(models.Model):
	"""Materialized eligible approvers for a given stage instance."""
	STATUS_PENDING = "pending"
	STATUS_APPROVED = "approved"
	STATUS_REJECTED = "rejected"
	STATUS_DELEGATED = "delegated"
	STATUS_CHOICES = [
		(STATUS_PENDING, "Pending"),
		(STATUS_APPROVED, "Approved"),
		(STATUS_REJECTED, "Rejected"),
		(STATUS_DELEGATED, "Delegated"),
	]
	stage_instance = models.ForeignKey(
		ApprovalWorkflowStageInstance, related_name="assignments", on_delete=models.CASCADE
	)
	user = models.ForeignKey(
		xx_User, related_name="approval_assignments", on_delete=models.CASCADE
	)
	role_snapshot = models.CharField(max_length=50, null=True, blank=True)
	level_snapshot = models.CharField(max_length=50, null=True, blank=True)
	is_mandatory = models.BooleanField(default=True)
 	status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "APPROVAL_ASSIGNMENT"
		unique_together = ("stage_instance", "user")
		indexes = [
			models.Index(fields=["user"]),
		]

	def __str__(self):
		return f"Assignment {self.user_id} -> StageInstance {self.stage_instance_id}"


class ApprovalAction(models.Model):
	"""Audit log of user actions within a stage instance."""

	ACTION_APPROVE = "approve"
	ACTION_REJECT = "reject"
	ACTION_DELEGATE = "delegate"
	ACTION_COMMENT = "comment"
	ACTION_CHOICES = [
		(ACTION_APPROVE, "Approve"),
		(ACTION_REJECT, "Reject"),
		(ACTION_DELEGATE, "Delegate"),
		(ACTION_COMMENT, "Comment"),
	]

	stage_instance = models.ForeignKey(
		ApprovalWorkflowStageInstance, related_name="actions", on_delete=models.CASCADE
	)
	user = models.ForeignKey(xx_User, related_name="approval_actions", on_delete=models.CASCADE)
	assignment = models.OneToOneField(ApprovalAssignment, null=True, blank=True, on_delete=models.SET_NULL, related_name="action")
 	action = models.CharField(max_length=10, choices=ACTION_CHOICES)
	comment = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	triggers_stage_completion = models.BooleanField(default=False)

	class Meta:
		db_table = "APPROVAL_ACTION"
		ordering = ["created_at"]
		indexes = [
			models.Index(fields=["stage_instance", "action"]),
		]

	def __str__(self):
		return f"Action {self.action} by {self.user_id} on StageInstance {self.stage_instance_id}"


class ApprovalDelegation(models.Model):
	"""Optional delegation record (future extension)."""

	from_user = models.ForeignKey(
		xx_User, related_name="delegations_given", on_delete=models.CASCADE
	)
	to_user = models.ForeignKey(
		xx_User, related_name="delegations_received", on_delete=models.CASCADE
	)
	stage_instance = models.ForeignKey(
		ApprovalWorkflowStageInstance, related_name="delegations", on_delete=models.CASCADE
	)
	active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	deactivated_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		db_table = "APPROVAL_DELEGATION"
		indexes = [
			models.Index(fields=["active"]),
		]

	def __str__(self):
		return f"Delegation {self.from_user_id}->{self.to_user_id} (StageInstance {self.stage_instance_id})"

	def deactivate(self):
		if self.active:
			self.active = False
			self.deactivated_at = timezone.now()
			self.save(update_fields=["active", "deactivated_at"])



from django.db import transaction
from django.utils import timezone

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
        active_stage = (
            workflow_instance.stage_instances
            .filter(status=ApprovalWorkflowStageInstance.STATUS_ACTIVE)
            .select_for_update()
            .first()
        )

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
        qs = qs.filter(level=required_level)
    if required_role:
        qs = qs.filter(role=required_role)

    for user in qs:
        ApprovalAssignment.objects.get_or_create(
            stage_instance=stage_instance,
            user=user,
            defaults={
                "role_snapshot": user.role,
                "level_snapshot": getattr(user.level, "name", None),
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

    # Lock current active stage(s)
    active_stages = (
        workflow_instance.stage_instances
        .filter(status=ApprovalWorkflowStageInstance.STATUS_ACTIVE)
        .select_for_update()
    )

    if not active_stages.exists():
        return False, "pending"

    # If multiple stages share a parallel_group, treat them as a group
    parallel_group = active_stages.first().stage_template.parallel_group
    if parallel_group:
        group_stages = workflow_instance.stage_instances.filter(
            status=ApprovalWorkflowStageInstance.STATUS_ACTIVE,
            stage_template__parallel_group=parallel_group,
        )
    else:
        group_stages = active_stages

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

        if stage.stage_template.decision_policy == ApprovalWorkflowStageTemplate.POLICY_ALL:
            if set(approved_assignments) != set(stage.assignments.values_list("id", flat=True)):
                all_approved = False


        elif stage.stage_template.decision_policy == ApprovalWorkflowStageTemplate.POLICY_ANY:
            if approved_assignments == 0:
                all_approved = False

        elif stage.stage_template.decision_policy == ApprovalWorkflowStageTemplate.POLICY_QUORUM:
            quorum = stage.stage_template.quorum_count or max(1, assignments.count() // 2 + 1)
            if approved_assignments < quorum:
                all_approved = False

        else:
            # Default safeguard: require at least one approval
            if approved_assignments == 0:
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
	if not active_stage.template.allow_reject and action == ApprovalAction.ACTION_REJECT:
		raise ValueError("Rejection not allowed in this stage")
	if not active_stage.template.allow_delegate and action == ApprovalAction.ACTION_DELEGATE:
		raise ValueError("Delegation not allowed in this stage")
    
    approvalAction.objects.create(
        stage_instance=active_stage,
        user=user,
        assignment=assignment,
        action=action,
        comment=comment,
        triggers_stage_completion=False,  # actual completion decided below
    )
	assignment.status = action
    assignment.save(update_fields=["status"])
    
    # 2) Handle delegation separately (optional)
    if action == ApprovalAction.ACTION_DELEGATE:
        # handle delegation logic if needed
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
