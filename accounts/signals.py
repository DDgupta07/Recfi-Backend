from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserWallet, DefaultWallet


@receiver(post_save, sender=UserWallet)
def check_default_wallet(sender, instance, created, **kwargs):
    if created:
        user_obj = instance.telegram_user
        default_wallet = DefaultWallet.objects.filter(telegram_user=user_obj).first()
        if not default_wallet:
            DefaultWallet.objects.create(telegram_user=user_obj, user_wallet=instance)
