from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .forms import EmailExistsPasswordResetForm, StyledSetPasswordForm


class PasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    html_email_template_name = 'accounts/password_reset_email_html.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    form_class = EmailExistsPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')
    from_email = settings.DEFAULT_FROM_EMAIL
    extra_email_context = {
        'site_name': '2c2d Solutions',
    }


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = StyledSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
