from pyexpat import model
from django.db import models
from user_management.models import xx_User
# Removed encrypted fields import - using standard Django fields now
import json


class xx_BudgetTransfer(models.Model):
    """Model to track budget transfers between users"""
    transaction_id = models.AutoField(primary_key=True)
    transaction_date = models.CharField(max_length=10)  # Changed from EncryptedCharField to DateField
    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Changed from EncryptedCharField to DecimalField
    status = models.CharField(max_length=10)
    requested_by = models.CharField(max_length=100, null=True, blank=True)  # Changed from EncryptedCharField
    user_id = models.IntegerField(null=True, blank=True)
    request_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)  # Changed from EncryptedCharField to TextField
    code = models.CharField(max_length=10, null=True, blank=True)
    gl_posting_status = models.CharField(max_length=50, null=True, blank=True)  # Changed from EncryptedCharField
    approvel_1 = models.CharField(max_length=100, null=True, blank=True)  # Changed from EncryptedCharField
    approvel_2 = models.CharField(max_length=100, null=True, blank=True)  # Changed from EncryptedCharField
    approvel_3 = models.CharField(max_length=100, null=True, blank=True)  # Changed from EncryptedCharField
    approvel_4 = models.CharField(max_length=100, null=True, blank=True)  # Changed from EncryptedCharField
    approvel_1_date = models.DateTimeField(null=True, blank=True)  # Changed from EncryptedDateTimeField
    approvel_2_date = models.DateTimeField(null=True, blank=True)  # Changed from EncryptedDateTimeField
    approvel_3_date = models.DateTimeField(null=True, blank=True)  # Changed from EncryptedDateTimeField
    approvel_4_date = models.DateTimeField(null=True, blank=True)  # Changed from EncryptedDateTimeField
    status_level = models.IntegerField(default=1)
    attachment = models.CharField(max_length=10, null=True, blank=True, default="No")  # Changed from EncryptedCharField
    fy = models.IntegerField(null=True, blank=True)  # Changed from EncryptedIntegerField
    group_id = models.IntegerField(null=True, blank=True)
    interface_id = models.IntegerField(null=True, blank=True)
    reject_group_id = models.IntegerField(null=True, blank=True)
    reject_interface_id = models.IntegerField(null=True, blank=True)
    approve_group_id = models.IntegerField(null=True, blank=True)
    approve_interface_id = models.IntegerField(null=True, blank=True)
    report = models.CharField(max_length=10, null=True, blank=True)  # Changed from EncryptedCharField
    type = models.CharField(max_length=10, null=True, blank=True)  # Changed from EncryptedCharField
    
    class Meta:
        db_table = 'XX_BUDGET_TRANSFER_XX'
    
    def __str__(self):
        return f"Transfer {self.transaction_id}: {self.amount} requested by {self.requested_by}"


class xx_BudgetTransferAttachment(models.Model):
    """Model to store file attachments as BLOBs for budget transfers"""
    attachment_id = models.AutoField(primary_key=True)
    budget_transfer = models.ForeignKey(
        xx_BudgetTransfer, 
        on_delete=models.CASCADE,
        related_name='attachments',
        db_column='transaction_id'
    )
    file_name = models.CharField(max_length=255)  # Changed from EncryptedCharField
    file_type = models.CharField(max_length=100)  # Changed from EncryptedCharField
    file_size = models.IntegerField()
    file_data = models.BinaryField()  # This will store the BLOB data
    upload_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'XX_BUDGET_TRANSFER_ATTACHMENT_XX'
        
    def __str__(self):
        return f"Attachment {self.attachment_id}: {self.file_name} for Transfer {self.budget_transfer_id}"


class xx_BudgetTransferRejectReason(models.Model):
    """Model to store reject reasons for budget transfers"""
    Transcation_id = models.ForeignKey(
        xx_BudgetTransfer,
        on_delete=models.CASCADE,
        related_name='reject_reasons'
    )
    reason_text = models.TextField(null=True, blank=True)  # Changed from EncryptedCharField to TextField

    reject_date = models.DateTimeField(auto_now_add=True)  # Changed from EncryptedDateTimeField

    reject_by = models.CharField(max_length=100, null=False, blank=True)  # Changed from EncryptedCharField


    class Meta:
        db_table = 'XX_BUDGET_TRANSFER_REJECT_REASON_XX'
        
    def __str__(self):
        return f"Reject Reason for Transfer {self.budget_transfer_id}: {self.reason_text}"




class xx_DashboardBudgetTransfer(models.Model):
    """Model to store dashboard data for budget transfers"""
    Dashboard_id = models.AutoField(primary_key=True)
    data = models.TextField(null=True, blank=True)  # Changed from EncryptedTextField - Store JSON as text
    date = models.DateTimeField(auto_now_add=True)  # Changed from EncryptedDateTimeField
    
    def set_data(self, data_dict):
        """Helper method to store dictionary as JSON string"""
        self.data = json.dumps(data_dict)
    
    def get_data(self):
        """Helper method to retrieve JSON data as dictionary"""
        if self.data:
            return json.loads(self.data)
        return None
    
    class Meta:
        db_table = 'XX_DASHBOARD_BUDGET_TRANSFER_XX'
    
    def __str__(self):
        return f"Dashboard Data {self.Dashboard_id} from {self.date}"