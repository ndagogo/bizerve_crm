from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Task

_previous_task_status = {}


@receiver(pre_save, sender=Task)
def capture_task_status_for_notifications(sender, instance, **kwargs):
    if instance.pk:
        try:
            _previous_task_status[instance.pk] = Task.objects.get(pk=instance.pk).status
        except Task.DoesNotExist:
            _previous_task_status[instance.pk] = None


@receiver(post_save, sender=Task)
def notify_on_task_events(sender, instance, created, **kwargs):
    """Create in-app notifications for key task events."""
    from notifications.models import Notification

    if created:
        Notification.objects.create(
            user=instance.assigned_to,
            message=f"New task assigned: {instance.title}",
            notification_type='email',
            related_task=instance,
        )
        return

    prev_status = _previous_task_status.pop(instance.pk, None)
    if prev_status == instance.status:
        return

    notifications = {
        'completed': (instance.created_by, f"Task completed and awaiting approval: {instance.title}"),
        'approved': (instance.assigned_to, f"Task approved: {instance.title}"),
        'queried': (instance.assigned_to, f"Task queried — action required: {instance.title}"),
        'declined': (instance.created_by, f"Task declined: {instance.title}"),
    }

    if instance.status in notifications:
        user, message = notifications[instance.status]
        Notification.objects.create(
            user=user,
            message=message,
            notification_type='email',
            related_task=instance,
        )
