from rest_framework import serializers

from .models import PaymentIntent


class InitializePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=100)


class VerifyPaymentSerializer(serializers.Serializer):
    reference = serializers.CharField()


class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = ['id', 'reference', 'amount', 'status', 'created_at']
        read_only_fields = fields

class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=100)
    bank_code = serializers.CharField(max_length=10)
    account_number = serializers.CharField(max_length=10)        