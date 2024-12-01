from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import CryptoTrade, Recifi
from base.constants import WALLET_ADDRESS_REQ


class CryptoTradeSerializer(serializers.ModelSerializer):
    """
    Serializer for the CryptoTrade model.
    """

    telegram_user_id = serializers.CharField(
        error_messages={"required": "Telegram user id is required."}
    )

    class Meta:
        model = CryptoTrade
        fields = ["telegram_user_id", "trade_type", "quantity", "target_price"]
        extra_kwargs = {
            "trade_type": {"error_messages": {"required": "Trade type is required."}},
            "quantity": {"error_messages": {"required": "Quantity is required."}},
            "target_price": {
                "error_messages": {"required": "Target price is required."}
            },
        }

    def validate_trade_type(self, value):
        """
        Validates the trade type value.
        """
        if value not in ["buy", "sell"]:
            raise serializers.ValidationError(
                "Trade type should be either buy or sell."
            )
        return value

    def validate_quantity(self, value):
        """
        Validates the quantity value.
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity should be greater than 0.")
        return value

    def validate_target_price(self, value):
        """
        Validates the target price value.
        """
        if value <= 0:
            raise serializers.ValidationError("Target price should be greater than 0.")
        return value

    def validate(self, attrs):
        trade_type = attrs.get("trade_type")
        quantity = attrs.get("quantity")
        if trade_type == "buy" and quantity < 1:
            raise serializers.ValidationError("Minimum 1 USDT is required to buy ETH.")
        return super().validate(attrs)


class CryptoTradeGetSerializer(serializers.ModelSerializer):
    """
    Serializer for the CryptoTrade model.
    """

    class Meta:
        model = CryptoTrade
        fields = ["uuid", "trade_type", "quantity", "target_price", "status"]


class recifierializer(serializers.ModelSerializer):
    """
    Serializer for the Recifi model.
    """

    class Meta:
        model = Recifi
        fields = [
            "name",
            "wallet_address",
            "percentage_change_24hrs",
            "pecentage_change_7days",
            "percentage_change_30days",
            "pecentage_change_1year",
        ]


class Addrecifierializer(serializers.ModelSerializer):
    """
    Serializer for the Recifi model. Valid for only POST method.
    """

    class Meta:
        model = Recifi
        fields = ["name", "wallet_address"]
        extra_kwargs = {
            "name": {"required": False},
            "wallet_address": {
                "validators": [
                    UniqueValidator(
                        queryset=Recifi.objects.all(),
                        message="Provided wallet address is already exists in our Recifi whales wallets.",
                    )
                ],
                "error_messages": {"required": WALLET_ADDRESS_REQ},
            },
        }

    def validate_wallet_address(self, value):
        """
        Validates the wallet address value.
        """
        if len(value) != 42:
            raise serializers.ValidationError("Kindly provide correct wallet address.")
        return value

    def validate(self, attrs):
        """
        Provide name for wallet address if not provided by user
        """
        name = attrs.get("name")
        if not name:
            wallet_count = Recifi.objects.count()
            attrs["name"] = f"Wallet {wallet_count + 1}"
        return attrs
