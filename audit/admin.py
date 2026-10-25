from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'model_name', 'message', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('message', 'user__username')
    readonly_fields = ('created_at',)
