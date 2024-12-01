from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.conf import settings

from base.models import BaseModel
from utils.w3 import check_balance


# Create your models here.


class TelegramUser(BaseModel):
    telegram_user_id = models.CharField(max_length=255, unique=True)
    phone_no = models.CharField(max_length=15, null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.telegram_user_id


class UserWallet(BaseModel):
    telegram_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="user_wallet"
    )
    wallet_name = models.CharField(max_length=255)
    wallet_phrase_key = ArrayField(
        models.CharField(max_length=255), blank=True, null=True
    )
    wallet_address = models.CharField(max_length=50)
    private_key = models.CharField(max_length=250)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.wallet_name

    def get_etherscan_url(self):
        """
        Constructs the Etherscan URL for the wallet.

        Returns:
            str: Etherscan URL for the wallet address.
        """
        return f"{settings.ETHERSCAN_URL}{self.wallet_address}"

    def get_balance(self):
        """
        Retrieves the balance of the wallet.

        Returns:
            float: Balance of the wallet.
        """
        return check_balance(self.wallet_address)


class DefaultWallet(BaseModel):
    telegram_user = models.OneToOneField(
        TelegramUser, on_delete=models.CASCADE, related_name="default_wallet"
    )
    user_wallet = models.OneToOneField(UserWallet, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.telegram_user.telegram_user_id
