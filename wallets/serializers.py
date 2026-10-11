from rest_framework import serializers

from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'account_number', 'balance', 'currency', 'is_active', 'created_at']
        read_only_fields = fields