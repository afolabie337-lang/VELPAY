import uuid
from django.conf import settings
from django.db import models

from wallets.models import Wallet


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        TRANSFER = 'transfer', 'Transfer'
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=40, unique=True)

    sender_wallet = models.ForeignKey(
        Wallet, on_delete=models.PROTECT, related_name='sent_transactions',
        null=True, blank=True,
    )
    receiver_wallet = models.ForeignKey(
        Wallet, on_delete=models.PROTECT, related_name='received_transactions',
        null=True, blank=True,
    )

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} — {self.amount} ({self.status})"