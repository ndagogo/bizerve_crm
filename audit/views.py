from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import role_required
from .models import AuditLog


@login_required
@role_required('super_admin', 'admin')
def audit_log(request):
    logs = AuditLog.objects.select_related('user')[:200]
    return render(request, 'audit/log.html', {'logs': logs})
