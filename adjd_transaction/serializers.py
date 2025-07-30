from rest_framework import serializers

from account_and_entitys.models import XX_ACCOUNT_ENTITY_LIMIT
from .models import xx_TransactionTransfer

class AdjdTransactionTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = xx_TransactionTransfer
        fields = '__all__'

    def validate(self, attrs):
        account_code = int(attrs.get('account_code'))
        cost_center_code = int(attrs.get('cost_center_code'))
        from_center = attrs.get('from_center', 0)
        to_center = attrs.get('to_center', 0)
        # C0202001, 416220
        # If required fields are missing, raise an error
        if not account_code or not cost_center_code:
            raise serializers.ValidationError("Account code and cost center code are required.")

        # Try to get the limit entry, but if it doesn't exist, allow the transfer
        try:
            limit = XX_ACCOUNT_ENTITY_LIMIT.objects.get(
                account_id=account_code,
                entity_id=cost_center_code
            )
        except XX_ACCOUNT_ENTITY_LIMIT.DoesNotExist:
            # No limit found → transfer is allowed
            return attrs

        # Validate source transfer
        if from_center and from_center > 0:
            if limit.is_transer_allowed_for_source != 'Yes':
                raise serializers.ValidationError("Transfers from this account and cost center are not allowed.")

        # Validate target transfer
        if to_center and to_center > 0:
            if limit.is_transer_allowed_for_target != 'Yes':
                raise serializers.ValidationError("Transfers to this account and cost center are not allowed.")

        # Validate both directions
        if (from_center and from_center > 0) or (to_center and to_center > 0):
            if limit.is_transer_allowed != 'Yes':
                raise serializers.ValidationError("Transfers between this account and cost center are not allowed.")

        return attrs
