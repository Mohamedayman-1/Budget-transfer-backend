from django.db import models
from user_management.models import xx_User
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField

class xx_BudgetTransfer(models.Model):
    """Model to track budget transfers between users"""
    transaction_id = models.AutoField(primary_key=True)
    transaction_date = EncryptedCharField(max_length=10)
    amount = models.FloatField()
    status = EncryptedCharField(max_length=10)
    requested_by = EncryptedCharField(max_length=10)
    user_id = models.IntegerField(null=True, blank=True)
    request_date = models.DateTimeField(auto_now_add=True)
    notes = EncryptedCharField(max_length=500,null=True, blank=True)
    description_x = models.TextField(max_length=500,null=True, blank=True)
    code = EncryptedCharField(max_length=10, null=True, blank=True)
    gl_posting_status = EncryptedCharField(max_length=10, null=True, blank=True)
    approvel_1 = EncryptedCharField(max_length=10, null=True, blank=True)
    approvel_2 = EncryptedCharField(max_length=10, null=True, blank=True)
    approvel_3 = EncryptedCharField(max_length=10, null=True, blank=True)
    approvel_4 = EncryptedCharField(max_length=10, null=True, blank=True)
    approvel_1_date = models.DateTimeField(null=True, blank=True)
    approvel_2_date = models.DateTimeField(null=True, blank=True)
    approvel_3_date = models.DateTimeField(null=True, blank=True)
    approvel_4_date = models.DateTimeField(null=True, blank=True)
    status_level = models.IntegerField(default=1)
    attachment = EncryptedCharField(max_length=10, null=True, blank=True,default="No")
    fy = EncryptedCharField(max_length=10, null=True, blank=True)
    group_id = models.IntegerField(null=True, blank=True)
    interface_id = models.IntegerField(null=True, blank=True)
    reject_group_id = models.IntegerField(null=True, blank=True)
    reject_interface_id = models.IntegerField(null=True, blank=True)
    approve_group_id = models.IntegerField(null=True, blank=True)
    approve_interface_id = models.IntegerField(null=True, blank=True)
    report = EncryptedCharField(max_length=10, null=True, blank=True)  # This one is already small
    type = EncryptedCharField(max_length=10, null=True, blank=True)
    
    class Meta:
        db_table = 'XX_BUDGET_TRANSFER'
    
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
    file_name = EncryptedCharField(max_length=255)
    file_type = EncryptedCharField(max_length=100)
    file_size = models.IntegerField()
    file_data = models.BinaryField()  # This will store the BLOB data
    upload_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'XX_BUDGET_TRANSFER_ATTACHMENT'
        
    def __str__(self):
        return f"Attachment {self.attachment_id}: {self.file_name} for Transfer {self.budget_transfer_id}"


class xx_BudgetTransferRejectReason(models.Model):
    """Model to store reject reasons for budget transfers"""
    Transcation_id = models.ForeignKey(
        xx_BudgetTransfer,
        on_delete=models.CASCADE,
        related_name='reject_reasons'
    )
    reason_text = EncryptedCharField(max_length=500,null=True, blank=True)

    reject_date = models.DateTimeField(auto_now_add=True)

    reject_by = EncryptedCharField(max_length=25, null=False, blank=True)


    class Meta:
        db_table = 'XX_BUDGET_TRANSFER_REJECT_REASON'
        
    def __str__(self):
        return f"Reject Reason for Transfer {self.budget_transfer_id}: {self.reason_text}"
