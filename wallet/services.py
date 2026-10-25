from wallet.models import Transaction, Wallet


def credit_task_payment(task):
    """
    Credit staff wallet for an approved task. Idempotent — skips if already paid.
    Returns True when a new payment was created.
    """
    if not task.amount or task.amount <= 0:
        return False

    staff_wallet, _ = Wallet.objects.get_or_create(user=task.assigned_to)
    already_paid = Transaction.objects.filter(
        wallet=staff_wallet,
        task=task,
        transaction_type='credit',
    ).exists()
    if already_paid:
        return False

    description = f"Payment for completed task: {task.title}"
    staff_wallet.credit(task.amount, description, task)
    return True
