from tasks.models import Task
from wallet.models import Wallet


def sidebar_context(request):
    """Provide shared navigation context for authenticated users."""
    if not request.user.is_authenticated:
        return {}

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    context = {
        'sidebar_wallet_balance': wallet.balance,
        'sidebar_task_count': Task.objects.count(),
        'sidebar_unread_notifications': 0,
    }

    if request.user.user_type in ('super_admin', 'admin'):
        context['total_count'] = Task.objects.count()
    elif request.user.user_type == 'staff':
        context['total_count'] = Task.objects.filter(assigned_to=request.user).count()
    elif request.user.user_type == 'partner':
        context['total_count'] = Task.objects.filter(created_by=request.user).count()
    else:
        context['total_count'] = 0

    try:
        from notifications.models import Notification
        context['sidebar_unread_notifications'] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
    except Exception:
        pass

    return context
