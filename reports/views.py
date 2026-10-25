from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import User
from tasks.models import Task
from wallet.models import Transaction, WithdrawalRequest


@login_required
@role_required('super_admin', 'admin')
def report_list(request):
    total_users = User.objects.count()
    tasks_by_status = Task.objects.values('status').annotate(count=Count('id')).order_by('status')
    total_revenue = Transaction.objects.filter(transaction_type='credit').aggregate(
        total=Sum('amount')
    )['total'] or 0
    pending_withdrawals = WithdrawalRequest.objects.filter(status='pending').count()
    active_tasks = Task.objects.exclude(status__in=['approved', 'declined']).count()

    context = {
        'total_users': total_users,
        'tasks_by_status': tasks_by_status,
        'total_revenue': total_revenue,
        'pending_withdrawals': pending_withdrawals,
        'active_tasks': active_tasks,
        'total_tasks': Task.objects.count(),
    }
    return render(request, 'reports/list.html', context)
