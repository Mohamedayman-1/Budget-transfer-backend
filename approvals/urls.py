from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    # Workflow Management APIs
    path('start-workflow/', views.StartApprovalWorkflowAPIView.as_view(), name='start_workflow'),
    path('create-workflow/', views.CreateWorkflowInstanceAPIView.as_view(), name='create_workflow'),
    path('cancel-workflow/', views.CancelWorkflowAPIView.as_view(), name='cancel_workflow'),
    path('activate-next-stage/<int:budget_transfer_id>/', views.ActivateNextStageAPIView.as_view(), name='activate_next_stage'),
    
    # User Action APIs
    path('process-action/<int:budget_transfer_id>/', views.ProcessUserActionAPIView.as_view(), name='process_action'),
    path('delegate/', views.DelegateApprovalAPIView.as_view(), name='delegate_approval'),
    
    # Status Check APIs
    path('check-stage-status/<int:budget_transfer_id>/', views.CheckFinishedStageAPIView.as_view(), name='check_stage_status'),
    path('pending-approvals/', views.GetUserPendingApprovalsAPIView.as_view(), name='pending_approvals'),
    
    # Workflow Information APIs
    path('templates/', views.ApprovalWorkflowTemplateListAPIView.as_view(), name='workflow_templates'),
    path('workflow-instance/<int:pk>/', views.ApprovalWorkflowInstanceDetailAPIView.as_view(), name='workflow_instance_detail'),
    path('workflow-by-transfer/<int:budget_transfer_id>/', views.ApprovalWorkflowInstanceByBudgetTransferAPIView.as_view(), name='workflow_by_transfer'),
    
    # Template Management APIs
    path('templates/create/', views.CreateWorkflowTemplateAPIView.as_view(), name='create_template'),
    path('templates/<int:pk>/update/', views.UpdateWorkflowTemplateAPIView.as_view(), name='update_template'),
    path('templates/<int:pk>/delete/', views.DeleteWorkflowTemplateAPIView.as_view(), name='delete_template'),
    path('templates/<int:template_id>/stages/', views.GetTemplateStagesAPIView.as_view(), name='template_stages'),
    path('templates/<int:template_id>/stages/reorder/', views.ReorderStageTemplatesAPIView.as_view(), name='reorder_stages'),
    
    # Stage Management APIs
    path('templates/<int:template_id>/stages/create/', views.CreateStageTemplateAPIView.as_view(), name='create_stage'),
    path('templates/<int:template_id>/stages/bulk-create/', views.BulkCreateStagesAPIView.as_view(), name='bulk_create_stages'),
    path('stages/<int:pk>/update/', views.UpdateStageTemplateAPIView.as_view(), name='update_stage'),
    path('stages/<int:pk>/delete/', views.DeleteStageTemplateAPIView.as_view(), name='delete_stage'),
]
