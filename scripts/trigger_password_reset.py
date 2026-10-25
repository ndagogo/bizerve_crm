"""
Quick local check for forgot-password email sending.

Usage (from project root):
  python scripts/trigger_password_reset.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_process.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from accounts.forms import EmailExistsPasswordResetForm

User = get_user_model()

username = 'testuser'
email = 'test@example.com'

user, created = User.objects.get_or_create(
    username=username,
    defaults={'email': email, 'user_type': 'staff'},
)
if created:
    user.set_password('testpassword')
    user.save()
    print('Created test user:', username)
else:
    if not user.email:
        user.email = email
        user.save(update_fields=['email'])
    print('Test user exists:', username, '->', user.email)

form = EmailExistsPasswordResetForm({'email': user.email})
if form.is_valid():
    form.save(
        domain_override='127.0.0.1:8000',
        subject_template_name='accounts/password_reset_subject.txt',
        email_template_name='accounts/password_reset_email.html',
        html_email_template_name='accounts/password_reset_email_html.html',
        use_https=False,
        from_email=None,
        request=None,
        extra_email_context={'site_name': '2c2d Solutions'},
    )
    print('Password reset email sent.')
    print('Check the console output and/or tmp/email_outbox/')
else:
    print('Form invalid:', form.errors)
