from django.utils.deprecation import MiddlewareMixin

from .models import AuditLog


class AuditMiddleware(MiddlewareMixin):
    """Log authenticated POST requests for audit trail."""

    EXCLUDED_PATHS = ('/static/', '/media/', '/admin/jsi18n/')

    def process_response(self, request, response):
        if not request.user.is_authenticated:
            return response
        if request.method != 'POST':
            return response
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response

        ip = request.META.get('REMOTE_ADDR')
        AuditLog.objects.create(
            user=request.user,
            action='update',
            message=f"{request.method} {request.path} -> {response.status_code}",
            ip_address=ip,
        )
        return response
