"""Apply pending migrations before production starts serving requests.

Railway's pre-deploy step did not create accounts_sessionpolicy, so the
portal hit a missing-table error. Running migrate here uses the same
process, settings, and DATABASE_URL as the running site.
"""

from django.conf import settings
from django.core.management import call_command


def apply_pending_migrations():
    """Migrate before serving, including when production still has DEBUG on."""
    engine = settings.DATABASES['default']['ENGINE']
    if settings.DEBUG and engine.endswith('sqlite3'):
        return
    print('Applying database migrations before serving requests.', flush=True)
    call_command('migrate', interactive=False, verbosity=1)
    print('Database migrations finished.', flush=True)
