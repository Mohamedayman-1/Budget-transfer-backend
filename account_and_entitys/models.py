from django.db import models

class XX_Account(models.Model):
    """Model representing ADJD accounts"""
    account = models.CharField(max_length=255, unique=True)
    parent = models.CharField(max_length=50, null=True, blank=True)
    alias_default = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.account
    
    class Meta:
     db_table = 'XX_Account'

class XX_Entity(models.Model):
    """Model representing ADJD entities"""
    entity = models.CharField(max_length=50)
    parent = models.CharField(max_length=50, null=True, blank=True)
    alias_default = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.entity
    
    class Meta:
     db_table = 'XX_Entity'


class XX_PivotFund(models.Model):
    """Model representing ADJD pivot funds"""
    entity = models.CharField(max_length=50)
    account = models.CharField(max_length=50)
    year = models.IntegerField()
    actual = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    fund = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    budget = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    encumbrance = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['entity', 'account', 'year'], 
                name='unique_entity_account_year'
            )
        ]
        db_table = 'XX_PivotFund'

class XX_TransactionAudit(models.Model):
    """Model representing ADJD transaction audit records"""
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    transfer_id = models.IntegerField(null=True, blank=True)
    transcation_code = models.CharField(max_length=50, null=True, blank=True)
    cost_center_code = models.CharField(max_length=50, null=True, blank=True)
    account_code = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f"Audit {self.id}: {self.transcation_code}"
    
    class Meta:
        db_table = 'XX_ADJD_TRANSACTION_AUDIT'


class XX_ACCOUNT_ENTITY_LIMIT(models.Model):
    """Model representing ADJD account entity limits"""
    id = models.AutoField(primary_key=True)
    account_id = models.CharField(max_length=255)
    entity_id = models.CharField(max_length=255)
    is_transer_allowed_for_source = models.CharField(max_length=255, null=True, blank=True)
    is_transer_allowed_for_target = models.CharField(max_length=255, null=True, blank=True)
    is_transer_allowed = models.CharField(max_length=255, null=True, blank=True)
    source_count = models.IntegerField(null=True, blank=True)   
    target_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Account Entity Limit {self.id}" 


    class Meta:
        db_table = 'XX_ACCOUNT_ENTITY_LIMIT'
        unique_together = ('account_id', 'entity_id')


