import random

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Wallet


def generate_account_number():
    while True:
        number = str(random.randint(1000000000, 9999999999))
        if not Wallet.objects.filter(account_number=number).exists():
            return number


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet_for_new_user(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance, account_number=generate_account_number())