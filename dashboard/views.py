from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from tasks.models import Task, TaskComment
from wallet.models import Wallet, Transaction


@login_required
def dashboard(request):
    """Dashboard view with live statistics."""
    user = request.user
    context = {
        'user': user,
        'recent_activity': [],
    }

    role_titles = {
        'super_admin': 'Super Admin Dashboard',
        'admin': 'Admin Dashboard',
        'staff': 'Staff Dashboard',
        'partner': 'Partner Portal',
    }
    context['dashboard_type'] = user.user_type
    context['dashboard_title'] = role_titles.get(user.user_type, 'Dashboard')

    wallet, _ = Wallet.objects.get_or_create(user=user)
    context['wallet_balance'] = wallet.balance

    if user.user_type in ('super_admin', 'admin'):
        context.update({
            'total_users': user.__class__.objects.count(),
            'active_tasks': Task.objects.exclude(status__in=['approved', 'declined']).count(),
            'pending_approval': Task.objects.filter(status='completed').count(),
            'total_revenue': Transaction.objects.filter(transaction_type='credit').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'total_tasks': Task.objects.count(),
        })
    elif user.user_type == 'staff':
        assigned = Task.objects.filter(assigned_to=user)
        context.update({
            'assigned_count': assigned.count(),
            'completed_count': assigned.filter(status='approved').count(),
            'in_progress_count': assigned.filter(status__in=['accepted', 'processing']).count(),
            'due_today_count': assigned.filter(
                expected_completion__date=timezone.now().date()
            ).exclude(status__in=['completed', 'approved']).count(),
        })
    elif user.user_type == 'partner':
        created = Task.objects.filter(created_by=user)
        context.update({
            'jobs_submitted': created.count(),
            'jobs_completed': created.filter(status='approved').count(),
            'jobs_in_progress': created.exclude(status__in=['approved', 'declined']).count(),
            'total_spent': created.filter(status='approved').aggregate(
                total=Sum('amount')
            )['total'] or 0,
        })

    context['recent_activity'] = TaskComment.objects.select_related(
        'task', 'user'
    ).order_by('-created_at')[:8]

    return render(request, 'dashboard/premium.html', context)
