from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AdminLevel

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'user_type', 'is_verified', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {
            'fields': (
                'user_type', 'is_verified', 'is_active', 
                'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
        }),
        ('Wallet & Security', {'fields': ('wallet_balance', 'tfa_enabled')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2', 
                'first_name', 'last_name', 'phone', 'user_type'
            ),
        }),
    )
    
    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Full Name'

@admin.register(AdminLevel)
class AdminLevelAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'user_type', 'level_display', 'is_active', 'created_at')
    list_filter = ('level', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'username', 'full_name', 'user_type')
    list_select_related = ('user',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'full_name', 'user_type')
        }),
        ('Admin Level Configuration', {
            'fields': ('user', 'level', 'is_active', 'permissions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def username(self, obj):
        return obj.user.username
    username.short_description = 'Username'
    
    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'Full Name'
    
    def user_type(self, obj):
        return obj.user.get_user_type_display()
    user_type.short_description = 'User Type'
    
    def level_display(self, obj):
        return obj.get_level_display()
    level_display.short_description = 'Access Level'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(
                user_type__in=['super_admin', 'admin', 'staff']
            ).order_by('username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)