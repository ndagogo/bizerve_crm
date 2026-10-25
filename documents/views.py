from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from tasks.models import TaskDocument


@login_required
def document_list(request):
    user = request.user
    documents = TaskDocument.objects.select_related('task', 'uploaded_by')

    if user.user_type == 'staff':
        documents = documents.filter(task__assigned_to=user)
    elif user.user_type == 'partner':
        documents = documents.filter(task__created_by=user)
    elif user.user_type not in ('super_admin', 'admin'):
        documents = documents.none()

    context = {'documents': documents.order_by('-uploaded_at')[:100]}
    return render(request, 'documents/list.html', context)
