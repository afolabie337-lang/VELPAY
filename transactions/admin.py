from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'transaction_type', 'amount', 'status', 'sender_wallet', 'receiver_wallet', 'created_at']
    list_filter = ['transaction_type', 'status']
    search_fields = ['reference', 'sender_wallet__account_number', 'receiver_wallet__account_number']
    readonly_fields = ['id', 'created_at', 'updated_at']