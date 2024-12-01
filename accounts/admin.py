from django.contrib import admin

from .models import DefaultWallet, TelegramUser, UserWallet

# Register your models here.


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("uuid", "telegram_user_id", "phone_no", "otp", "created_at")


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "telegram_user",
        "wallet_name",
        "wallet_address",
        "is_verified",
        "created_at",
    )
    readonly_fields = ("private_key", "wallet_address")


@admin.register(DefaultWallet)
class DefaultWalletAdmin(admin.ModelAdmin):
    list_display = ("telegram_user", "user_wallet", "wallet_name", "created_at")

    def wallet_name(self, obj):
        return obj.user_wallet.wallet_name
