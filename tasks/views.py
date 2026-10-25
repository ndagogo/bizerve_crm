from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Task, TaskDocument, TaskComment
from .forms import TaskCreateForm, TaskUpdateForm, TaskQueryForm, TaskDocumentForm, TaskCommentForm, TaskDeclineForm
from .utils import user_can_view_task, user_can_comment_on_task


@login_required
def task_list(request):
    """Display tasks based on user role"""
    user = request.user
    tasks = Task.objects.all()
    
    # Filter based on user role
    if user.user_type == 'staff':
        tasks = tasks.filter(assigned_to=user)
    elif user.user_type == 'partner':
        tasks = tasks.filter(created_by=user)
    # Admins and super admins see all tasks
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Calculate status counts for the current user
    if user.user_type == 'staff':
        all_user_tasks = Task.objects.filter(assigned_to=user)
    elif user.user_type == 'partner':
        all_user_tasks = Task.objects.filter(created_by=user)
    else:
        all_user_tasks = Task.objects.all()
    
    status_counts = {
        'pending': all_user_tasks.filter(status='pending').count(),
        'accepted': all_user_tasks.filter(status='accepted').count(),
        'declined': all_user_tasks.filter(status='declined').count(),
        'processing': all_user_tasks.filter(status='processing').count(),
        'completed': all_user_tasks.filter(status='completed').count(),
        'approved': all_user_tasks.filter(status='approved').count(),
        'queried': all_user_tasks.filter(status='queried').count(),
    }
    
    # Add these count calculations
    context = {
        'tasks': tasks,
        'total_count': tasks.count(),
        'pending_count': tasks.filter(status='pending').count(),
        'accepted_count': tasks.filter(status='accepted').count(),
        'processing_count': tasks.filter(status='processing').count(),
        'completed_count': tasks.filter(status='completed').count(),
        'approved_count': tasks.filter(status='approved').count(),
        'queried_count': tasks.filter(status='queried').count(),
        'declined_count': tasks.filter(status='declined').count(),
        'current_status': request.GET.get('status', ''),
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, task_id):
    """View task details and handle actions"""
    task = get_object_or_404(Task, id=task_id)

    if not user_can_view_task(request.user, task):
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('tasks:task_list')

    documents = task.documents.all()
    comments = task.comments.all()
    
    # Check permissions
    can_edit = request.user == task.created_by or request.user.user_type in ['super_admin', 'admin']
    can_accept = task.can_accept() and request.user == task.assigned_to
    can_decline = task.can_decline() and request.user == task.assigned_to  # Staff can decline / reject task
    can_complete = task.can_complete() and request.user == task.assigned_to
    can_approve = task.can_approve() and request.user == task.created_by
    
    # Forms
    document_form = TaskDocumentForm()
    comment_form = TaskCommentForm()
    query_form = TaskQueryForm()
    
    if request.method == 'POST':
        if not user_can_comment_on_task(request.user, task):
            messages.error(request, 'You do not have permission to modify this task.')
            return redirect('tasks:task_detail', task_id=task.id)

        if 'add_comment' in request.POST:
            comment_form = TaskCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.task = task
                comment.user = request.user
                comment.save()
                
                # Add system note
                TaskComment.objects.create(
                    task=task,
                    user=request.user,
                    comment=f"{request.user.get_full_name()} added a comment",
                    is_system_note=True
                )
                
                messages.success(request, 'Comment added successfully!')
                return redirect('tasks:task_detail', task_id=task.id)
        
        elif 'upload_document' in request.POST:
            document_form = TaskDocumentForm(request.POST, request.FILES)
            if document_form.is_valid():
                document = document_form.save(commit=False)
                document.task = task
                document.uploaded_by = request.user
                document.save()
                
                messages.success(request, 'Document uploaded successfully!')
                return redirect('tasks:task_detail', task_id=task.id)
    
    context = {
        'task': task,
        'documents': documents,
        'comments': comments,
        'document_form': document_form,
        'comment_form': comment_form,
        'query_form': query_form,
        'can_edit': can_edit,
        'can_accept': can_accept,
        'can_decline': can_decline,
        'can_complete': can_complete,
        'can_approve': can_approve,
    }
    return render(request, 'tasks/task_detail.html', context)

@login_required
def create_task(request):
    """Create a new task"""
    if request.user.user_type not in ['super_admin', 'admin']:
        messages.error(request, 'You do not have permission to create tasks.')
        return redirect('tasks:task_list')
    
    if request.method == 'POST':
        form = TaskCreateForm(request.POST, request=request)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            # Add system note
            TaskComment.objects.create(
                task=task,
                user=request.user,
                comment=f"Task created by {request.user.get_full_name()} and assigned to {task.assigned_to.get_full_name()}",
                is_system_note=True
            )
            
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskCreateForm(request=request)
    
    context = {
        'form': form,
        'title': 'Create New Task'
    }
    return render(request, 'tasks/task_form.html', context)

@login_required
def update_task(request, task_id):
    """Update an existing task"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if request.user != task.created_by and request.user.user_type not in ['super_admin', 'admin']:
        messages.error(request, 'You do not have permission to edit this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        form = TaskUpdateForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            
            # Add system note
            TaskComment.objects.create(
                task=task,
                user=request.user,
                comment=f"Task updated by {request.user.get_full_name()}",
                is_system_note=True
            )
            
            messages.success(request, 'Task updated successfully!')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskUpdateForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'title': f'Update Task: {task.title}'
    }
    return render(request, 'tasks/task_form.html', context)

@login_required
def accept_task(request, task_id):
    """Staff accepts a task"""
    task = get_object_or_404(Task, id=task_id)
    
    if not task.can_accept() or request.user != task.assigned_to:
        messages.error(request, 'You cannot accept this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    task.status = 'accepted'
    task.accepted_at = timezone.now()
    task.save()
    
    # Add system note
    TaskComment.objects.create(
        task=task,
        user=request.user,
        comment=f"Task accepted by {request.user.get_full_name()}",
        is_system_note=True
    )
    
    messages.success(request, 'Task accepted successfully!')
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def start_task(request, task_id):
    """Staff starts working on a task"""
    task = get_object_or_404(Task, id=task_id)
    
    if task.status != 'accepted' or request.user != task.assigned_to:
        messages.error(request, 'You cannot start this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    task.status = 'processing'
    task.started_at = timezone.now()
    task.save()
    
    # Add system note
    TaskComment.objects.create(
        task=task,
        user=request.user,
        comment=f"Task started by {request.user.get_full_name()}",
        is_system_note=True
    )
    
    messages.success(request, 'Task started! You are now working on this task.')
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def complete_task(request, task_id):
    """Staff marks task as completed"""
    task = get_object_or_404(Task, id=task_id)
    
    if not task.can_complete() or request.user != task.assigned_to:
        messages.error(request, 'You cannot complete this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save()
    
    # Add system note
    TaskComment.objects.create(
        task=task,
        user=request.user,
        comment=f"Task completed by {request.user.get_full_name()} - Awaiting approval",
        is_system_note=True
    )
    
    messages.success(request, 'Task completed! Waiting for admin approval.')
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def approve_task(request, task_id):
    """Admin approves completed task"""
    task = get_object_or_404(Task, id=task_id)
    
    if not task.can_approve() or request.user != task.created_by:
        messages.error(request, 'You cannot approve this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    # Store old status
    old_status = task.status
    
    task.status = 'approved'
    task.approved_at = timezone.now()
    task.save()

    if old_status != 'approved' and task.amount > 0:
        messages.success(
            request,
            f'Task approved successfully! ${task.amount} will be credited to staff wallet.',
        )
    else:
        messages.success(request, 'Task approved successfully!')
    
    # Add approval system note
    TaskComment.objects.create(
        task=task,
        user=request.user,
        comment=f"Task approved by {request.user.get_full_name()}",
        is_system_note=True
    )
    
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def query_task(request, task_id):
    """Admin queries a completed task"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.user != task.created_by and request.user.user_type not in ['super_admin', 'admin']:
        messages.error(request, 'You cannot query this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        form = TaskQueryForm(request.POST)
        if form.is_valid():
            task.status = 'queried'
            task.query_reason = form.cleaned_data['reason']
            task.queried_at = timezone.now()  # Add this line
            task.save()
            
            # Add system note
            TaskComment.objects.create(
                task=task,
                user=request.user,
                comment=f"Task queried by {request.user.get_full_name()}. Reason: {task.query_reason}",
                is_system_note=True
            )
            
            messages.warning(request, 'Task has been queried. Staff needs to make modifications.')
            return redirect('tasks:task_detail', task_id=task.id)
    
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def delete_task(request, task_id):
    """Delete a task (only for admins and task creators)"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.user != task.created_by and request.user.user_type not in ['super_admin', 'admin']:
        messages.error(request, 'You do not have permission to delete this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('tasks:task_list')
    
    context = {'task': task}
    return render(request, 'tasks/task_confirm_delete.html', context)


@login_required
def decline_task(request, task_id):
    """Staff declines a task with reason"""
    task = get_object_or_404(Task, id=task_id)
    
    if not task.can_decline() or request.user != task.assigned_to:
        messages.error(request, 'You cannot decline this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        # Get the reason from POST data directly
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, 'Please provide a reason for declining the task.')
            return redirect('tasks:task_detail', task_id=task.id)
        
        task.status = 'declined'
        task.decline_reason = reason
        task.declined_at = timezone.now()
        task.save()
        
        # Add system note
        TaskComment.objects.create(
            task=task,
            user=request.user,
            comment=f"Task declined by {request.user.get_full_name()}. Reason: {task.decline_reason}",
            is_system_note=True
        )
        
        messages.warning(request, 'Task has been declined.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    # If GET request, redirect to task detail (modal will handle the form)
    return redirect('tasks:task_detail', task_id=task.id)
    