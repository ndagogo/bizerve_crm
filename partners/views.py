from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from tasks.models import Task


@login_required
def partner_dashboard(request):
    if request.user.user_type != 'partner':
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Partner access only.')
        return redirect('dashboard:dashboard')

    tasks = Task.objects.filter(created_by=request.user)
    stats = {
        'total': tasks.count(),
        'pending': tasks.filter(status='pending').count(),
        'in_progress': tasks.exclude(status__in=['approved', 'declined', 'pending']).count(),
        'completed': tasks.filter(status='approved').count(),
    }
    recent_tasks = tasks.order_by('-created_at')[:10]

    return render(request, 'partners/dashboard.html', {
        'stats': stats,
        'recent_tasks': recent_tasks,
    })
