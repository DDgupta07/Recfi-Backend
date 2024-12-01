from django.contrib import admin

from .models import CryptoTrade, Recifi, RecifiToken


# Register your models here.


@admin.register(CryptoTrade)
class CryptoTradeAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_user",
        "user_wallet",
        "trade_type",
        "quantity",
        "target_price",
        "status",
        "created_at",
    )


@admin.register(Recifi)
class RecifiAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "name",
        "wallet_address",
        "percentage_change_24hrs",
        "pecentage_change_7days",
        "percentage_change_30days",
        "pecentage_change_1year",
        "created_at",
    )


@admin.register(RecifiToken)
class RecifiTokenAdmin(admin.ModelAdmin):
    list_display = ("uuid", "Recifi", "token_address", "created_at")
