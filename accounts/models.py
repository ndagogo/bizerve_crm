from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    USER_TYPES = (
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('partner', 'Partner'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='staff')
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tfa_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        full_name = self.get_full_name().strip()
        if full_name:
            return f"{full_name} ({self.username}) - {self.get_user_type_display()}"
        return f"{self.username} - {self.get_user_type_display()}"
    
    def clean(self):
        """Validate that super_admin users are also staff and superuser"""
        if self.user_type == 'super_admin' and not (self.is_staff and self.is_superuser):
            raise ValidationError('Super Admin users must have both staff and superuser status.')

class AdminLevel(models.Model):
    LEVEL_CHOICES = [
        (1, 'Level 1 - Basic Access'),
        (2, 'Level 2 - Moderate Access'), 
        (3, 'Level 3 - Advanced Access'),
        (4, 'Level 4 - Full Access'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'user_type__in': ['super_admin', 'admin', 'staff']},
        verbose_name="Admin User"
    )
    level = models.IntegerField(choices=LEVEL_CHOICES, default=1, verbose_name="Access Level")
    permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom permissions in JSON format"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Admin Level"
        verbose_name_plural = "Admin Levels"
        ordering = ['-level', 'user__username']
    
    def __str__(self):
        return f"{self.user.username} - Level {self.level} ({self.get_level_display()})"
    
    def clean(self):
        """Validate admin level assignments"""
        if self.user.user_type not in ['super_admin', 'admin', 'staff']:
            raise ValidationError('Admin levels can only be assigned to admin or staff users.')
        
        # Super admins should have highest level
        if self.user.user_type == 'super_admin' and self.level < 4:
            raise ValidationError('Super Admin users should have Level 4 access.')
    
    @property
    def username(self):
        return self.user.username
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def user_type(self):
        return self.user.get_user_type_display()


class SessionPolicy(models.Model):
    """The one row that controls idle sign-out for every account."""

    inactivity_timeout_minutes = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        verbose_name='Inactivity limit (minutes)',
        help_text='Sign users out after this many minutes without a request. Use 1 to 1,440.',
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name='Sign out after inactivity',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Session policy'
        verbose_name_plural = 'Session policy'

    def __str__(self):
        if not self.is_enabled:
            return 'Inactivity sign-out is off'
        return f'Sign out after {self.inactivity_timeout_minutes} idle minutes'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        policy, _created = cls.objects.get_or_create(pk=1)
        return policy