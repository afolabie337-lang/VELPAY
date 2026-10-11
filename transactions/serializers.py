from rest_framework import serializers

from .models import Transaction


class TransferSerializer(serializers.Serializer):
    receiver_account_number = serializers.CharField(max_length=10)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=1)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'reference', 'transaction_type', 'status', 'amount',
            'sender_wallet', 'receiver_wallet', 'description', 'created_at',
        ]
        read_only_fields = fields