from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*roles):
    """Restrict view access to users whose user_type is in roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.user_type not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
