from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve


def healthz(request):
    return HttpResponse('ok', content_type='text/plain')


urlpatterns = [
    path('healthz', healthz, name='healthz'),
    path('healthz/', healthz, name='healthz-slash'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('tasks/', include('tasks.urls')),
    path('partners/', include('partners.urls')),
    path('wallet/', include('wallet.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/', include('api.urls')),
    path('reports/', include('reports.urls')),
    path('documents/', include('documents.urls')),
    path('notifications/', include('notifications.urls')),
    path('audit/', include('audit.urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)