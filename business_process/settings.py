import os
from pathlib import Path

import dj_database_url
from decouple import config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Railway injects RAILWAY_ENVIRONMENT on every deploy. Local runs leave it unset,
# so the same settings file keeps SQLite, DEBUG, and HTTP cookies on your machine.
ON_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT'))


def _csv(value):
    return [item.strip() for item in value.split(',') if item.strip()]


DEBUG = config('DEBUG', default=not ON_RAILWAY, cast=bool)

_INSECURE_SECRET_KEY = 'django-insecure-change-this-in-production-!'
SECRET_KEY = config('SECRET_KEY', default=_INSECURE_SECRET_KEY)
if not DEBUG and SECRET_KEY == _INSECURE_SECRET_KEY:
    raise ImproperlyConfigured(
        'Set a unique SECRET_KEY in the environment when DEBUG is False.'
    )

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,0.0.0.0,crm.auxanosoft.com',
    cast=_csv,
)

# Railway's edge and health checker use hostnames that are not in the local .env.
# crm.auxanosoft.com is the public custom domain. It is not a *.railway.app host,
# so it has to be listed here or Django rejects the request.
CUSTOM_HOSTS = ('crm.auxanosoft.com',)
if ON_RAILWAY:
    for host in ('.railway.app', '.up.railway.app', 'healthcheck.railway.app', *CUSTOM_HOSTS):
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
    public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '').strip()
    if public_domain and public_domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(public_domain)

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=_csv)
if ON_RAILWAY:
    for origin in (
        'https://*.up.railway.app',
        'https://*.railway.app',
        *(f'https://{host}' for host in CUSTOM_HOSTS),
    ):
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)
    public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '').strip()
    if public_domain:
        origin = f'https://{public_domain}'
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',
    'channels',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    
    # Local apps
    'accounts',
    'tasks',
    'documents',
    'notifications',
    'wallet',
    'partners',
    'dashboard',
    'api',
    'reports',
    'audit',
    
    


]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'business_process.urls'
WSGI_APPLICATION = 'business_process.wsgi.application'

# Channels configuration.
# In-memory is enough for local runserver. A Railway Redis service sets REDIS_URL.
ASGI_APPLICATION = 'business_process.asgi.application'
REDIS_URL = config('REDIS_URL', default='')
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.sidebar_context',
            ],
        },
    },
]

# Postgres on Railway arrives as DATABASE_URL. Leave that unset locally and
# Django keeps using SQLite (or the DB_* variables in .env).
_database_url = config('DATABASE_URL', default='')
if ON_RAILWAY and not _database_url:
    raise ImproperlyConfigured(
        'Set DATABASE_URL on Railway to the Postgres service URL, '
        'for example ${{Postgres.DATABASE_URL}}.'
    )
if _database_url:
    DATABASES = {
        'default': dj_database_url.parse(
            _database_url,
            conn_max_age=config('DB_CONN_MAX_AGE', default=600, cast=int),
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
            'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
            'USER': config('DB_USER', default=''),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default=''),
            'PORT': config('DB_PORT', default=''),
        }
    }

# Celery Configuration
_local_redis = 'redis://localhost:6379/0'
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=REDIS_URL or _local_redis)
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=REDIS_URL or _local_redis)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Static files. WhiteNoise serves collected files on Railway.
# Finders stay on locally so runserver works without collectstatic.
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
_static_dir = BASE_DIR / 'static'
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
WHITENOISE_USE_FINDERS = DEBUG

# Media files. A Railway volume sets RAILWAY_VOLUME_MOUNT_PATH; local files stay in /media.
MEDIA_URL = '/media/'
_volume_mount = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', '').strip()
if _volume_mount:
    MEDIA_ROOT = Path(_volume_mount) / 'media'
else:
    MEDIA_ROOT = BASE_DIR / 'media'

# Email configuration
# Development: prints to the runserver console AND saves under tmp/email_outbox/
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='accounts.email_backends.DevelopmentEmailBackend',
)
EMAIL_FILE_PATH = BASE_DIR / 'tmp' / 'email_outbox'
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='2c2d Solutions <noreply@2c2d.local>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Two-Factor Authentication
# LOGIN_URL = 'two_factor:login'
LOGIN_REDIRECT_URL = '/dashboard/'

# Login/Logout redirects
LOGIN_REDIRECT_URL = '/dashboard/'  # Redirect to dashboard after login
LOGOUT_REDIRECT_URL = '/'           # Redirect to home after logout

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Railway terminates TLS at its proxy. Redirects stay off so the platform
# health check (plain HTTP inside the network) still receives 200.
if ON_RAILWAY:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,
            },
        },
    }
