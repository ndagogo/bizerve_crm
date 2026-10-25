from django.contrib import admin
from .models import Wallet, Transaction, WithdrawalMethod, WithdrawalRequest


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'transaction_type', 'description', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__username', 'description')
    readonly_fields = ('created_at',)


@admin.register(WithdrawalMethod)
class WithdrawalMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'withdrawal_type', 'is_active', 'minimum_amount', 'fee_type')
    list_filter = ('withdrawal_type', 'is_active', 'fee_type')
    search_fields = ('name',)


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'net_amount', 'status', 'created_at')
    list_filter = ('status', 'withdrawal_method')
    search_fields = ('user__username', 'bank_name', 'account_number')
    readonly_fields = ('created_at', 'updated_at', 'processed_at')
