from rest_framework import serializers
from .models import xx_AdjdTransactionTransfer

class AdjdTransactionTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = xx_AdjdTransactionTransfer
        fields = '__all__'
