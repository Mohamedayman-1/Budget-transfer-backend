from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ApprovalWorkflowTemplate,
    ApprovalWorkflowStageTemplate,
    ApprovalWorkflowInstance,
    ApprovalWorkflowStageInstance,
    ApprovalAssignment,
    ApprovalAction,
    ApprovalDelegation
)
from user_management.models import xx_User, xx_UserLevel
from budget_management.models import xx_BudgetTransfer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for responses"""
    class Meta:
        model = xx_User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']

class UserLevelSerializer(serializers.ModelSerializer):
    """User level serializer"""
    class Meta:
        model = xx_UserLevel
        fields = ['id', 'name', 'level_order']

class ApprovalWorkflowStageTemplateSerializer(serializers.ModelSerializer):
    """Stage template serializer"""
    required_user_level = UserLevelSerializer(read_only=True)
    
    class Meta:
        model = ApprovalWorkflowStageTemplate
        fields = '__all__'

class ApprovalWorkflowTemplateSerializer(serializers.ModelSerializer):
    """Workflow template serializer with stages"""
    stages = ApprovalWorkflowStageTemplateSerializer(many=True, read_only=True)
    
    class Meta:
        model = ApprovalWorkflowTemplate
        fields = '__all__'

class ApprovalActionSerializer(serializers.ModelSerializer):
    """Approval action serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ApprovalAction
        fields = '__all__'

class ApprovalAssignmentSerializer(serializers.ModelSerializer):
    """Approval assignment serializer"""
    user = UserSerializer(read_only=True)
    actions = ApprovalActionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ApprovalAssignment
        fields = '__all__'

class ApprovalWorkflowStageInstanceSerializer(serializers.ModelSerializer):
    """Stage instance serializer"""
    stage_template = ApprovalWorkflowStageTemplateSerializer(read_only=True)
    assignments = ApprovalAssignmentSerializer(many=True, read_only=True)
    actions = ApprovalActionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ApprovalWorkflowStageInstance
        fields = '__all__'

class ApprovalWorkflowInstanceSerializer(serializers.ModelSerializer):
    """Workflow instance serializer"""
    template = ApprovalWorkflowTemplateSerializer(read_only=True)
    current_stage_template = ApprovalWorkflowStageTemplateSerializer(read_only=True)
    stage_instances = ApprovalWorkflowStageInstanceSerializer(many=True, read_only=True)
    
    class Meta:
        model = ApprovalWorkflowInstance
        fields = '__all__'

class BudgetTransferBasicSerializer(serializers.ModelSerializer):
    """Basic budget transfer info for approval context"""
    class Meta:
        model = xx_BudgetTransfer
        fields = ['id', 'transfer_amount', 'transfer_date', 'description', 'status']

class ApprovalDelegationSerializer(serializers.ModelSerializer):
    """Delegation serializer"""
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    stage_instance = ApprovalWorkflowStageInstanceSerializer(read_only=True)
    
    class Meta:
        model = ApprovalDelegation
        fields = '__all__'

# Request/Response Serializers for API endpoints

class ProcessActionRequestSerializer(serializers.Serializer):
    """Request serializer for processing user actions"""
    action = serializers.ChoiceField(choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('delegate', 'Delegate'),
        ('comment', 'Comment')
    ])
    comment = serializers.CharField(required=False, allow_blank=True, max_length=500)

class StartWorkflowRequestSerializer(serializers.Serializer):
    """Request serializer for starting workflow"""
    budget_transfer_id = serializers.IntegerField()
    transfer_type = serializers.ChoiceField(
        choices=[('FAR', 'FAR'), ('AFR', 'AFR'), ('FAD', 'FAD'), ('GEN', 'Generic')],
        required=False
    )

class CreateWorkflowRequestSerializer(serializers.Serializer):
    """Request serializer for creating workflow instance"""
    budget_transfer_id = serializers.IntegerField()
    transfer_type = serializers.ChoiceField(
        choices=[('FAR', 'FAR'), ('AFR', 'AFR'), ('FAD', 'FAD'), ('GEN', 'Generic')],
        required=False
    )

class CancelWorkflowRequestSerializer(serializers.Serializer):
    """Request serializer for cancelling workflow"""
    budget_transfer_id = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)

class DelegateApprovalRequestSerializer(serializers.Serializer):
    """Request serializer for delegating approval"""
    to_user_id = serializers.IntegerField()
    stage_instance_id = serializers.IntegerField()
    comment = serializers.CharField(required=False, allow_blank=True, max_length=500)

class WorkflowStatusResponseSerializer(serializers.Serializer):
    """Response serializer for workflow status operations"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    workflow_instance = ApprovalWorkflowInstanceSerializer(required=False)
    stage_finished = serializers.BooleanField(required=False)
    outcome = serializers.CharField(required=False)

class PendingApprovalsResponseSerializer(serializers.Serializer):
    """Response serializer for pending approvals"""
    count = serializers.IntegerField()
    assignments = ApprovalAssignmentSerializer(many=True)
    budget_transfers = BudgetTransferBasicSerializer(many=True)

# Template Creation Serializers

class CreateWorkflowTemplateSerializer(serializers.ModelSerializer):
    """Serializer for creating new workflow templates"""
    
    class Meta:
        model = ApprovalWorkflowTemplate
        fields = ['code', 'transfer_type', 'name', 'description', 'is_active', 'version']
        
    def validate_code(self, value):
        """Ensure code is unique"""
        if ApprovalWorkflowTemplate.objects.filter(code=value).exists():
            raise serializers.ValidationError("A template with this code already exists.")
        return value

class CreateStageTemplateSerializer(serializers.ModelSerializer):
    """Serializer for creating new stage templates"""
    
    class Meta:
        model = ApprovalWorkflowStageTemplate
        fields = [
            'workflow_template', 'order_index', 'name', 'decision_policy',
            'quorum_count', 'required_user_level', 
            'dynamic_filter_json', 'allow_reject', 'allow_delegate',
            'sla_hours', 'parallel_group'
        ]
        
    def validate(self, data):
        """Custom validation for stage creation"""
        # Validate quorum_count for QUORUM policy
        if data.get('decision_policy') == ApprovalWorkflowStageTemplate.POLICY_QUORUM:
            if not data.get('quorum_count') or data['quorum_count'] < 1:
                raise serializers.ValidationError(
                    "quorum_count must be provided and greater than 0 for QUORUM policy"
                )
        
        # Validate unique order_index per workflow_template
        workflow_template = data.get('workflow_template')
        order_index = data.get('order_index')
        
        if workflow_template and order_index:
            if ApprovalWorkflowStageTemplate.objects.filter(
                workflow_template=workflow_template,
                order_index=order_index
            ).exists():
                raise serializers.ValidationError(
                    f"Stage with order_index {order_index} already exists for this template"
                )
        
        return data

class BulkCreateStagesSerializer(serializers.Serializer):
    """Serializer for creating multiple stages at once"""
    workflow_template_id = serializers.IntegerField()
    stages = CreateStageTemplateSerializer(many=True)
    
    def validate_workflow_template_id(self, value):
        """Ensure template exists"""
        try:
            ApprovalWorkflowTemplate.objects.get(id=value)
        except ApprovalWorkflowTemplate.DoesNotExist:
            raise serializers.ValidationError("Workflow template does not exist.")
        return value
    
    def validate_stages(self, value):
        """Validate stages list"""
        if not value:
            raise serializers.ValidationError("At least one stage must be provided.")
        
        # Check for duplicate order_index values
        order_indices = [stage.get('order_index') for stage in value]
        if len(order_indices) != len(set(order_indices)):
            raise serializers.ValidationError("Duplicate order_index values found in stages.")
        
        return value

class UpdateWorkflowTemplateSerializer(serializers.ModelSerializer):
    """Serializer for updating workflow templates"""
    
    class Meta:
        model = ApprovalWorkflowTemplate
        fields = ['name', 'description', 'is_active']

class UpdateStageTemplateSerializer(serializers.ModelSerializer):
    """Serializer for updating stage templates"""
    
    class Meta:
        model = ApprovalWorkflowStageTemplate
        fields = [
            'name', 'decision_policy', 'quorum_count', 'required_user_level',
            'required_role', 'dynamic_filter_json', 'allow_reject',
            'allow_delegate', 'sla_hours', 'parallel_group'
        ]
        
    def validate(self, data):
        """Custom validation for stage updates"""
        # Validate quorum_count for QUORUM policy
        decision_policy = data.get('decision_policy', self.instance.decision_policy)
        if decision_policy == ApprovalWorkflowStageTemplate.POLICY_QUORUM:
            quorum_count = data.get('quorum_count', self.instance.quorum_count)
            if not quorum_count or quorum_count < 1:
                raise serializers.ValidationError(
                    "quorum_count must be provided and greater than 0 for QUORUM policy"
                )
        
        return data
