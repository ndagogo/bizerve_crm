def user_can_view_task(user, task):
    """Return True if the user is allowed to view the given task."""
    if user.user_type in ('super_admin', 'admin'):
        return True
    return task.assigned_to_id == user.id or task.created_by_id == user.id


def user_can_comment_on_task(user, task):
    """Return True if the user may add comments or upload documents."""
    return user_can_view_task(user, task)
