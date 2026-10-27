from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import AdminPasswordForm, SessionPolicyForm, UserAccountForm
from .models import SessionPolicy, User


def _managed_users(actor):
    users = User.objects.all()
    if actor.user_type != 'super_admin':
        users = users.exclude(user_type='super_admin')
    return users


def _can_manage(actor, target):
    if actor.user_type == 'super_admin':
        return True
    if actor.user_type == 'admin' and target.user_type != 'super_admin':
        return True
    return False


@login_required
@role_required('super_admin', 'admin')
def user_list(request):
    role = request.GET.get('role', '').strip()
    status = request.GET.get('status', '').strip()
    query = request.GET.get('q', '').strip()

    users = _managed_users(request.user)
    if role in dict(User.USER_TYPES):
        users = users.filter(user_type=role)
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone__icontains=query)
        )

    users = users.order_by('-created_at', 'username')
    page = Paginator(users, 20).get_page(request.GET.get('page'))
    counts = _managed_users(request.user)
    context = {
        'page_obj': page,
        'users': page.object_list,
        'query': query,
        'current_role': role,
        'current_status': status,
        'role_choices': (
            User.USER_TYPES
            if request.user.user_type == 'super_admin'
            else [choice for choice in User.USER_TYPES if choice[0] != 'super_admin']
        ),
        'total_count': counts.count(),
        'active_count': counts.filter(is_active=True).count(),
        'inactive_count': counts.filter(is_active=False).count(),
        'admin_count': counts.filter(user_type__in=['super_admin', 'admin']).count(),
        'session_policy': SessionPolicy.load(),
    }
    return render(request, 'accounts/users/list.html', context)


@login_required
@role_required('super_admin', 'admin')
def session_settings(request):
    policy = SessionPolicy.load()
    form = SessionPolicyForm(request.POST or None, instance=policy)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Session timeout updated.')
        return redirect('accounts:session_settings')
    return render(request, 'accounts/users/session_settings.html', {
        'form': form,
        'policy': policy,
    })


@login_required
@role_required('super_admin', 'admin')
def user_create(request):
    form = UserAccountForm(request.POST or None, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, f'Created user {user.username}.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/users/form.html', {
        'form': form,
        'title': 'Add user',
        'submit_label': 'Create user',
    })


@login_required
@role_required('super_admin', 'admin')
def user_edit(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not _can_manage(request.user, target):
        messages.error(request, 'You cannot edit this user.')
        return redirect('accounts:user_list')
    form = UserAccountForm(request.POST or None, instance=target, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Updated {target.username}.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/users/form.html', {
        'form': form,
        'title': f'Edit {target.username}',
        'submit_label': 'Save changes',
        'managed_user': target,
    })


@login_required
@role_required('super_admin', 'admin')
def user_password(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if not _can_manage(request.user, target):
        messages.error(request, 'You cannot change this password.')
        return redirect('accounts:user_list')
    form = AdminPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        target.set_password(form.cleaned_data['new_password1'])
        target.save(update_fields=['password'])
        messages.success(request, f'Password updated for {target.username}.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/users/password.html', {
        'form': form,
        'managed_user': target,
    })


@require_POST
@login_required
@role_required('super_admin', 'admin')
def user_toggle_active(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('accounts:user_list')
    if not _can_manage(request.user, target):
        messages.error(request, 'You cannot change this user.')
        return redirect('accounts:user_list')
    if (
        target.is_active
        and target.user_type == 'super_admin'
        and not User.objects.filter(user_type='super_admin', is_active=True).exclude(pk=target.pk).exists()
    ):
        messages.error(request, 'At least one active super admin is required.')
        return redirect('accounts:user_list')

    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    state = 'activated' if target.is_active else 'deactivated'
    messages.success(request, f'{target.username} was {state}.')
    return redirect('accounts:user_list')
