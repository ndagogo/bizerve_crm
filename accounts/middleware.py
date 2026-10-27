from django.contrib.auth import logout
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


LAST_ACTIVITY_SESSION_KEY = 'last_activity'


def idle_timeout_seconds():
    """Return the idle limit in seconds, or None when idle sign-out is off."""
    from accounts.models import SessionPolicy

    try:
        policy = SessionPolicy.load()
    except (OperationalError, ProgrammingError):
        return 30 * 60
    if not policy.is_enabled:
        return None
    return policy.inactivity_timeout_minutes * 60


class InactivityTimeoutMiddleware:
    """End a signed-in session after the admin-configured idle period."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            timeout = idle_timeout_seconds()
            if timeout is not None:
                now = timezone.now().timestamp()
                last_activity = request.session.get(LAST_ACTIVITY_SESSION_KEY)
                if last_activity is not None and now - float(last_activity) > timeout:
                    logout(request)
                    return _expired_response(request)
                request.session[LAST_ACTIVITY_SESSION_KEY] = now
        return self.get_response(request)


def _expired_response(request):
    login_url = reverse('accounts:login')
    if _wants_json(request):
        return JsonResponse(
            {'detail': 'You were signed out after a period of inactivity.'},
            status=401,
        )
    return redirect(f'{login_url}?session=expired')


def _wants_json(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return True
    accept = request.headers.get('accept', '')
    return 'application/json' in accept and 'text/html' not in accept
