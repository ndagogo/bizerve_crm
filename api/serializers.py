from rest_framework import serializers

from tasks.models import Task


class TaskSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'task_type', 'task_type_display', 'description',
            'status', 'status_display', 'priority', 'amount',
            'created_by', 'created_by_name', 'assigned_to', 'assigned_to_name',
            'expected_completion', 'actual_completion', 'created_at', 'updated_at',
        ]
        read_only_fields = fields
