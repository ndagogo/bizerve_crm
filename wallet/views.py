from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from accounts.decorators import role_required
from .models import Wallet, Transaction, WithdrawalRequest, WithdrawalMethod
from .forms import WithdrawalRequestForm, WithdrawalMethodForm


@login_required
def wallet_detail(request):
    """Display user's wallet and transaction history"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()[:20]
    withdrawal_requests = request.user.withdrawals.all()[:5]

    credit_count = wallet.transactions.filter(transaction_type='credit').count()
    debit_count = wallet.transactions.filter(transaction_type='debit').count()

    context = {
        'wallet': wallet,
        'transactions': transactions,
        'withdrawal_requests': withdrawal_requests,
        'credit_count': credit_count,
        'debit_count': debit_count,
    }
    return render(request, 'wallet/wallet_detail.html', context)


@login_required
def transaction_history(request):
    """Display full transaction history"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()

    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    return render(request, 'wallet/transaction_history.html', context)


@login_required
def withdrawal_request(request):
    """Handle withdrawal requests"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = WithdrawalRequestForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    withdrawal = form.save(commit=False)
                    withdrawal.user = request.user

                    method_type = withdrawal.withdrawal_method.withdrawal_type
                    if method_type == 'bank':
                        withdrawal.bank_name = form.cleaned_data['bank_name']
                        withdrawal.account_number = form.cleaned_data['account_number']
                        withdrawal.account_name = form.cleaned_data['account_name']
                    elif method_type == 'paypal':
                        withdrawal.paypal_email = form.cleaned_data['paypal_email']
                    elif method_type == 'crypto':
                        withdrawal.crypto_wallet = form.cleaned_data['crypto_wallet']
                    elif method_type == 'mobile_money':
                        withdrawal.mobile_number = form.cleaned_data['mobile_number']

                    withdrawal.save()

                    wallet.debit(
                        amount=withdrawal.amount,
                        description=f"Withdrawal request #{withdrawal.id} - {withdrawal.withdrawal_method.name}",
                        task=None,
                    )

                    messages.success(
                        request,
                        f"Withdrawal request submitted successfully! "
                        f"Net amount: ${withdrawal.net_amount} (Fee: ${withdrawal.fee})",
                    )
                    return redirect('wallet:wallet_detail')

            except Exception as e:
                messages.error(request, f"Withdrawal failed: {str(e)}")
    else:
        form = WithdrawalRequestForm(user=request.user)

    withdrawal_methods = WithdrawalMethod.objects.filter(is_active=True)

    context = {
        'form': form,
        'wallet': wallet,
        'withdrawal_methods': withdrawal_methods,
    }
    return render(request, 'wallet/withdrawal_request.html', context)


@login_required
def withdrawal_history(request):
    """Display user's withdrawal history"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    withdrawals = request.user.withdrawals.all()

    context = {
        'wallet': wallet,
        'withdrawals': withdrawals,
    }
    return render(request, 'wallet/withdrawal_history.html', context)


@login_required
def cancel_withdrawal(request, withdrawal_id):
    """Cancel a pending withdrawal request"""
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id, user=request.user)

    if not withdrawal.can_cancel():
        messages.error(request, "This withdrawal cannot be cancelled.")
        return redirect('wallet:withdrawal_history')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                wallet, _ = Wallet.objects.get_or_create(user=request.user)
                wallet.credit(
                    amount=withdrawal.amount,
                    description=f"Withdrawal cancellation #{withdrawal.id}",
                    task=None,
                )

                withdrawal.status = 'cancelled'
                withdrawal.save()

                messages.success(request, "Withdrawal cancelled successfully. Amount refunded to your wallet.")
                return redirect('wallet:withdrawal_history')

        except Exception as e:
            messages.error(request, f"Cancellation failed: {str(e)}")

    context = {'withdrawal': withdrawal}
    return render(request, 'wallet/cancel_withdrawal.html', context)


@login_required
@role_required('super_admin', 'admin')
def admin_withdrawal_list(request):
    """Admin view to manage withdrawal requests"""
    withdrawals = WithdrawalRequest.objects.all()
    status_filter = request.GET.get('status')

    if status_filter:
        withdrawals = withdrawals.filter(status=status_filter)

    context = {
        'withdrawals': withdrawals,
        'current_status': status_filter,
    }
    return render(request, 'wallet/admin_withdrawal_list.html', context)


@login_required
@role_required('super_admin', 'admin')
def admin_withdrawal_detail(request, withdrawal_id):
    """Admin view for withdrawal request details"""
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        previous_status = withdrawal.status

        if new_status in dict(WithdrawalRequest.STATUS_CHOICES):
            withdrawal.status = new_status
            withdrawal.admin_notes = admin_notes

            if new_status == 'completed':
                withdrawal.processed_at = timezone.now()

            if new_status == 'rejected' and previous_status not in ('rejected', 'cancelled'):
                wallet, _ = Wallet.objects.get_or_create(user=withdrawal.user)
                already_refunded = Transaction.objects.filter(
                    wallet=wallet,
                    transaction_type='credit',
                    description__contains=f"Withdrawal rejection #{withdrawal.id}",
                ).exists()
                if not already_refunded:
                    wallet.credit(
                        amount=withdrawal.amount,
                        description=f"Withdrawal rejection #{withdrawal.id} - refund",
                        task=None,
                    )

            withdrawal.save()
            messages.success(request, f"Withdrawal status updated to {withdrawal.get_status_display()}.")

        return redirect('wallet:admin_withdrawal_detail', withdrawal_id=withdrawal.id)

    context = {'withdrawal': withdrawal}
    return render(request, 'wallet/admin_withdrawal_detail.html', context)


@login_required
@role_required('super_admin', 'admin')
def admin_withdrawal_methods(request):
    """Admin view to manage withdrawal methods"""
    methods = WithdrawalMethod.objects.all()

    if request.method == 'POST':
        form = WithdrawalMethodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Withdrawal method created successfully.")
            return redirect('wallet:admin_withdrawal_methods')
    else:
        form = WithdrawalMethodForm()

    context = {
        'methods': methods,
        'form': form,
    }
    return render(request, 'wallet/admin_withdrawal_methods.html', context)


@login_required
@role_required('super_admin', 'admin')
def admin_edit_withdrawal_method(request, method_id):
    """Admin view to edit withdrawal methods"""
    method = get_object_or_404(WithdrawalMethod, id=method_id)

    if request.method == 'POST':
        form = WithdrawalMethodForm(request.POST, instance=method)
        if form.is_valid():
            form.save()
            messages.success(request, "Withdrawal method updated successfully.")
            return redirect('wallet:admin_withdrawal_methods')
    else:
        form = WithdrawalMethodForm(instance=method)

    context = {
        'method': method,
        'form': form,
    }
    return render(request, 'wallet/admin_edit_withdrawal_method.html', context)
