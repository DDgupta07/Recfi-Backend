from django.db import models
from base.models import BaseModel
from accounts.models import TelegramUser, UserWallet
from .enums import CryptoTradeChoices, TradeStatusChoices


# Create your models here.
class CryptoTrade(BaseModel):
    """
    Model representing a cryptocurrency trade entry for a user's trading activities.
    Inherits from BaseModel to include standard fields like uuid, created_at, updated_at, and deleted_at.
    """

    telegram_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="crypto_trade"
    )
    user_wallet = models.ForeignKey(
        UserWallet, on_delete=models.CASCADE, related_name="trade_wallet"
    )
    trade_type = models.CharField(choices=CryptoTradeChoices, max_length=50)
    quantity = models.FloatField()
    target_price = models.FloatField()
    status = models.CharField(choices=TradeStatusChoices, max_length=50, default="open")

    class Meta:
        ordering = ["-created_at"]


class Recifi(BaseModel):
    name = models.CharField(max_length=255)
    wallet_address = models.CharField(max_length=255)
    percentage_change_24hrs = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_change_7days = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    pecentage_change_7days = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_change_30days = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    percentage_change_30days = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_change_1year = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    pecentage_change_1year = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class RecifiToken(BaseModel):
    Recifi = models.ForeignKey(
        Recifi, on_delete=models.CASCADE, related_name="Recifi_token"
    )
    token_address = models.CharField(max_length=42)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.token_address
