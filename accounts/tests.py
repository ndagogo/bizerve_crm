from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.forms import EmailExistsPasswordResetForm
from accounts.models import SessionPolicy, User


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


class UserManagementDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='portaladmin',
            email='portal.admin@example.com',
            password='OldPass123!',
            user_type='admin',
        )
        self.staff = User.objects.create_user(
            username='portalstaff',
            email='portal.staff@example.com',
            password='OldPass123!',
            user_type='staff',
        )
        self.superuser = User.objects.create_user(
            username='portalsuper',
            email='portal.super@example.com',
            password='OldPass123!',
            user_type='super_admin',
            is_staff=True,
            is_superuser=True,
        )

    def test_staff_cannot_open_user_management(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('/admin/', response.url)

    def test_admin_sees_in_app_user_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Management')
        self.assertContains(response, 'portalstaff')
        self.assertNotContains(response, 'portalsuper')
        self.assertNotContains(response, '/admin/auth/user/')

    def test_admin_can_create_staff_user(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('accounts:user_create'), {
            'username': 'newstaff',
            'email': 'new.staff@example.com',
            'first_name': 'New',
            'last_name': 'Staff',
            'phone': '',
            'user_type': 'staff',
            'password1': 'NewPass123!',
            'password2': 'NewPass123!',
            'is_active': 'on',
        })
        self.assertRedirects(response, reverse('accounts:user_list'))
        created = User.objects.get(username='newstaff')
        self.assertTrue(created.check_password('NewPass123!'))
        self.assertEqual(created.user_type, 'staff')

    def test_admin_cannot_create_super_admin(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('accounts:user_create'), {
            'username': 'sneaky',
            'email': 'sneaky@example.com',
            'user_type': 'super_admin',
            'password1': 'NewPass123!',
            'password2': 'NewPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='sneaky').exists())

    def test_admin_cannot_deactivate_self_from_edit_form(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('accounts:user_edit', args=[self.admin.pk]), {
            'email': self.admin.email,
            'first_name': '',
            'last_name': '',
            'phone': '',
            'user_type': 'admin',
        })
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)


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


class SessionTimeoutTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username='idlestaff',
            email='idle.staff@example.com',
            password='OldPass123!',
            user_type='staff',
        )
        self.admin = User.objects.create_user(
            username='idleadmin',
            email='idle.admin@example.com',
            password='OldPass123!',
            user_type='admin',
        )
        self.policy = SessionPolicy.load()

    def _age_session(self, seconds):
        session = self.client.session
        session['last_activity'] = timezone.now().timestamp() - seconds
        session.save()

    def test_idle_user_is_signed_out(self):
        self.client.force_login(self.staff)
        self._age_session(self.policy.inactivity_timeout_minutes * 60 + 5)
        response = self.client.get(reverse('accounts:profile'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?session=expired")
        login_page = self.client.get(response.url)
        self.assertContains(login_page, 'inactivity')
        self.assertFalse(login_page.wsgi_request.user.is_authenticated)

    def test_recent_activity_keeps_the_session(self):
        self.client.force_login(self.staff)
        self._age_session(60)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertLess(
            timezone.now().timestamp() - self.client.session['last_activity'],
            5,
        )
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

    def test_disabled_policy_does_not_sign_out(self):
        self.policy.is_enabled = False
        self.policy.save()
        self.client.force_login(self.staff)
        self._age_session(24 * 60 * 60)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_admin_can_change_the_timeout(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('accounts:session_settings'), {
            'is_enabled': 'on',
            'inactivity_timeout_minutes': '15',
        })
        self.assertRedirects(response, reverse('accounts:session_settings'))
        self.policy.refresh_from_db()
        self.assertEqual(self.policy.inactivity_timeout_minutes, 15)
        self.assertTrue(self.policy.is_enabled)

    def test_staff_cannot_change_the_timeout(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('accounts:session_settings'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('/admin/', response.url)

    def test_timeout_outside_allowed_range_is_rejected(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('accounts:session_settings'), {
            'is_enabled': 'on',
            'inactivity_timeout_minutes': '5000',
        })
        self.assertEqual(response.status_code, 200)
        self.policy.refresh_from_db()
        self.assertEqual(self.policy.inactivity_timeout_minutes, 30)
