from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm


User = get_user_model()


class EmailExistsPasswordResetForm(PasswordResetForm):
    """Password reset form that verifies the email belongs to an active user."""

    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your account email',
            'autocomplete': 'email',
            'autofocus': True,
        }),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        matching_users = User.objects.filter(email__iexact=email)

        if not matching_users.exists():
            raise forms.ValidationError(
                "This email doesn't exist. Please check and try again."
            )

        if not matching_users.filter(is_active=True).exists():
            raise forms.ValidationError(
                "This account is inactive. Please contact an administrator."
            )

        return email


class StyledSetPasswordForm(SetPasswordForm):
    """Set-password form with Bootstrap-compatible widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'New password',
            'autocomplete': 'new-password',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        })
