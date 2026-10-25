from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks.models import Task
from .serializers import TaskSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_list_api(request):
    """Return tasks visible to the authenticated user."""
    user = request.user
    tasks = Task.objects.all()

    if user.user_type == 'staff':
        tasks = tasks.filter(assigned_to=user)
    elif user.user_type == 'partner':
        tasks = tasks.filter(created_by=user)

    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)

    serializer = TaskSerializer(tasks.order_by('-created_at')[:100], many=True)
    return Response({'count': tasks.count(), 'results': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_detail_api(request, task_id):
    """Return a single task if the user is allowed to view it."""
    from tasks.utils import user_can_view_task
    from django.shortcuts import get_object_or_404

    task = get_object_or_404(Task, id=task_id)
    if not user_can_view_task(request.user, task):
        return Response({'detail': 'Not found.'}, status=404)

    serializer = TaskSerializer(task)
    return Response(serializer.data)
