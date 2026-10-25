from django.contrib import admin
from .models import Task, TaskDocument, TaskComment

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'status', 'priority', 'created_by', 'assigned_to', 'created_at', 'is_overdue')
    list_filter = ('task_type', 'status', 'priority', 'created_at', 'assigned_to')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')
    readonly_fields = ('created_at', 'updated_at', 'accepted_at', 'started_at', 'completed_at', 'approved_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'task_type', 'description', 'priority')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to', 'expected_completion', 'amount')
        }),
        ('Status & Timeline', {
            'fields': ('status', 'query_reason', 'created_at', 'updated_at')
        }),
        ('Workflow Timestamps', {
            'fields': ('accepted_at', 'started_at', 'completed_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue(self, obj):
        return obj.is_overdue()
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

@admin.register(TaskDocument)
class TaskDocumentAdmin(admin.ModelAdmin):
    list_display = ('task', 'document_type', 'uploaded_by', 'uploaded_at', 'is_final')
    list_filter = ('document_type', 'uploaded_at', 'is_final')
    search_fields = ('task__title', 'document_type', 'description')

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'created_at', 'is_system_note')
    list_filter = ('is_system_note', 'created_at')
    search_fields = ('task__title', 'user__username', 'comment')
    readonly_fields = ('created_at',)