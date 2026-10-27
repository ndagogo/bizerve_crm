from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from .models import SessionPolicy


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


def apply_role_flags(user):
    """Keep Django staff flags aligned with the application role."""
    if user.user_type == 'super_admin':
        user.is_staff = True
        user.is_superuser = True
    else:
        user.is_staff = False
        user.is_superuser = False
    return user


class _BootstrapFieldsMixin:
    def _style_fields(self):
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if 'form-control' not in css and 'form-select' not in css and 'form-check-input' not in css:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = (css + ' form-check-input').strip()
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = (css + ' form-select').strip()
                else:
                    field.widget.attrs['class'] = (css + ' form-control').strip()


class UserAccountForm(_BootstrapFieldsMixin, forms.ModelForm):
    """Create or edit a portal user without opening Django Admin."""

    password1 = forms.CharField(
        label='Password',
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirm password',
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'phone',
            'user_type', 'is_verified', 'is_active',
        )

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.creating = self.instance.pk is None
        if not self.creating:
            self.fields.pop('password1')
            self.fields.pop('password2')
            self.fields['username'].disabled = True
        else:
            self.fields['password1'].required = True
            self.fields['password2'].required = True
        if actor is None or actor.user_type != 'super_admin':
            self.fields['user_type'].choices = [
                choice for choice in User.USER_TYPES if choice[0] != 'super_admin'
            ]
        self.fields['email'].required = True
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        taken = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            taken = taken.exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_user_type(self):
        user_type = self.cleaned_data['user_type']
        if self.actor and self.actor.user_type != 'super_admin' and user_type == 'super_admin':
            raise forms.ValidationError('Only a super admin can assign the Super Admin role.')
        if (
            self.instance.pk
            and self.instance.user_type == 'super_admin'
            and user_type != 'super_admin'
            and not User.objects.filter(user_type='super_admin', is_active=True).exclude(pk=self.instance.pk).exists()
        ):
            raise forms.ValidationError('At least one active super admin is required.')
        return user_type

    def clean(self):
        cleaned = super().clean()
        if self.creating:
            password1 = cleaned.get('password1')
            password2 = cleaned.get('password2')
            if password1 and password2 and password1 != password2:
                self.add_error('password2', 'The two password fields do not match.')
        if (
            self.instance.pk
            and self.actor
            and self.instance.pk == self.actor.pk
            and cleaned.get('is_active') is False
        ):
            self.add_error('is_active', 'You cannot deactivate your own account.')
        if (
            self.instance.pk
            and self.instance.is_active
            and cleaned.get('is_active') is False
            and self.instance.user_type == 'super_admin'
            and not User.objects.filter(user_type='super_admin', is_active=True).exclude(pk=self.instance.pk).exists()
        ):
            self.add_error('is_active', 'At least one active super admin is required.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.creating:
            user.set_password(self.cleaned_data['password1'])
        apply_role_flags(user)
        if commit:
            user.save()
        return user


class AdminPasswordForm(forms.Form):
    """Set another user's password from the portal."""

    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('new_password1')
        password2 = cleaned.get('new_password2')
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', 'The two password fields do not match.')
        return cleaned


class SessionPolicyForm(_BootstrapFieldsMixin, forms.ModelForm):
    """Let an admin choose how long an idle session stays signed in."""

    class Meta:
        model = SessionPolicy
        fields = ('is_enabled', 'inactivity_timeout_minutes')
        labels = {
            'is_enabled': 'Sign out after inactivity',
            'inactivity_timeout_minutes': 'Inactivity limit (minutes)',
        }
        help_texts = {
            'inactivity_timeout_minutes': 'Between 1 and 1,440 minutes (24 hours).',
        }
        widgets = {
            'inactivity_timeout_minutes': forms.NumberInput(attrs={'min': 1, 'max': 1440}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        minutes = self.fields['inactivity_timeout_minutes']
        minutes.min_value = 1
        minutes.widget.attrs['min'] = 1
        self._style_fields()


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
