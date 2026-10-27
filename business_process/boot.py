"""Apply pending migrations before production starts serving requests.

Railway's pre-deploy step did not create accounts_sessionpolicy, so the
portal hit a missing-table error. Running migrate here uses the same
process, settings, and DATABASE_URL as the running site.
"""

import logging

from django.conf import settings
from django.core.management import call_command


logger = logging.getLogger(__name__)


def apply_pending_migrations():
    if settings.DEBUG:
        return
    logger.warning('Applying database migrations before serving requests.')
    call_command('migrate', interactive=False, verbosity=1)
