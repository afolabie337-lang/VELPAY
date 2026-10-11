from django.contrib import admin

from .models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_number', 'balance', 'currency', 'is_active']
    search_fields = ['user__email', 'account_number']
    readonly_fields = ['id', 'created_at', 'updated_at']