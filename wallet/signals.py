from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Wallet

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.get_or_create(user=instance)


@receiver(post_save, sender=Wallet)
def sync_user_wallet_balance(sender, instance, **kwargs):
    """Keep legacy User.wallet_balance in sync with Wallet.balance."""
    User.objects.filter(pk=instance.user_id).update(wallet_balance=instance.balance)
