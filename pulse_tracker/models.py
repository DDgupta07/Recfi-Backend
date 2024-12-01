from django.db import models

from base.models import BaseModel
from accounts.models import TelegramUser


# Create your models here.


class WatchList(BaseModel):
    """
    Model representing a watchlist entry for a user's cryptocurrency interests.
    Inherits from BaseModel to include standard fields like uuid, created_at, updated_at, and deleted_at.
    """

    telegram_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="watchlist"
    )
    contract_address = models.CharField(max_length=75)
    symbol = models.CharField(max_length=20)
    percentage_change = models.IntegerField()

    class Meta:
        ordering = ["-created_at"]
