from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.forms import EmailExistsPasswordResetForm
from accounts.models import User


class PasswordResetFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='resetuser',
            email='reset.user@example.com',
            password='OldPass123!',
            user_type='staff',
        )

    def test_unknown_email_is_rejected(self):
        form = EmailExistsPasswordResetForm(data={'email': 'missing@example.com'})
        self.assertFalse(form.is_valid())
        self.assertIn("doesn't exist", form.errors['email'][0])

    def test_existing_email_is_accepted(self):
        form = EmailExistsPasswordResetForm(data={'email': 'reset.user@example.com'})
        self.assertTrue(form.is_valid())

    def test_inactive_user_email_is_rejected(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        form = EmailExistsPasswordResetForm(data={'email': 'reset.user@example.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('inactive', form.errors['email'][0].lower())


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='flowuser',
            email='flow.user@example.com',
            password='OldPass123!',
            user_type='staff',
        )

    def test_unknown_email_does_not_send_mail(self):
        form = EmailExistsPasswordResetForm(data={'email': 'nobody@example.com'})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(mail.outbox), 0)

    def test_existing_email_sends_reset_message(self):
        form = EmailExistsPasswordResetForm(data={'email': 'flow.user@example.com'})
        self.assertTrue(form.is_valid())
        form.save(
            domain_override='127.0.0.1:8000',
            subject_template_name='accounts/password_reset_subject.txt',
            email_template_name='accounts/password_reset_email.html',
            html_email_template_name='accounts/password_reset_email_html.html',
            use_https=False,
            from_email='noreply@2c2d.local',
            request=None,
            extra_email_context={'site_name': '2c2d Solutions'},
        )
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn('flow.user@example.com', message.to)
        self.assertIn('password', message.subject.lower())
        self.assertIn('password', message.body.lower())
        self.assertTrue(message.alternatives)
        self.assertIn('/accounts/reset/', message.body)


class UserManagementAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='usermgr',
            email='usermgr@example.com',
            password='OldPass123!',
        )
        self.client.force_login(self.admin)

    def test_auth_user_url_is_user_management(self):
        self.assertEqual(reverse('admin:accounts_user_changelist'), '/admin/auth/user/')
        self.assertEqual(reverse('admin:accounts_user_add'), '/admin/auth/user/add/')
        response = self.client.get('/admin/auth/user/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User management')
