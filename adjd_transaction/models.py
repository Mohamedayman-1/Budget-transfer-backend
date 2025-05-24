from django.db import models
from budget_management.models import xx_BudgetTransfer

class xx_AdjdTransactionTransfer(models.Model):
    """Model for ADJD transaction transfers"""
    transfer_id = models.AutoField(primary_key=True)
    cost_center_code = models.TextField(null=True, blank=True)
    account_name = models.TextField(null=True, blank=True)
    approved_budget = models.FloatField(null=True, blank=True)
    available_budget = models.FloatField(null=True, blank=True)
    from_center = models.FloatField(null=True, blank=True)
    to_center = models.FloatField(null=True, blank=True)
    transaction = models.ForeignKey(
        xx_BudgetTransfer,
        on_delete=models.CASCADE,
        db_column='transaction_id',
        null=True,
        blank=True,
        related_name='adjd_transfers'
    )
    reason = models.TextField(null=True, blank=True)
    account_code = models.TextField(null=True, blank=True)
    cost_center_name = models.TextField(null=True, blank=True)
    done = models.IntegerField(default=1)
    encumbrance = models.FloatField(null=True, blank=True)
    actual = models.FloatField(null=True, blank=True)
    # Additional file field for attachments
    file = models.FileField(upload_to='adjd_transfers/', null=True, blank=True)
    
    class Meta:
        db_table = 'xx_AdjdTransactionTransfer'
    
    def __str__(self):
        return f"ADJD Transfer {self.transfer_id}"
