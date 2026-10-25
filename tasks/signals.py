import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Task, TaskComment
from wallet.services import credit_task_payment

logger = logging.getLogger(__name__)

_previous_status = {}


@receiver(pre_save, sender=Task)
def capture_previous_task_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            prev = Task.objects.get(pk=instance.pk)
            _previous_status[instance.pk] = prev.status
        except Task.DoesNotExist:
            _previous_status[instance.pk] = None


@receiver(post_save, sender=Task)
def handle_task_approval_payment(sender, instance, created, **kwargs):
    """Credit staff wallet when task status changes to approved."""
    prev_status = _previous_status.pop(instance.pk, None)
    if created or prev_status == 'approved' or instance.status != 'approved':
        return

    try:
        if credit_task_payment(instance):
            TaskComment.objects.create(
                task=instance,
                user=instance.assigned_to,
                comment=(
                    f"Payment of ${instance.amount} credited to "
                    f"{instance.assigned_to.get_full_name()}'s wallet for task completion"
                ),
                is_system_note=True,
            )
    except Exception:
        logger.exception("Error crediting wallet for task %s", instance.pk)
