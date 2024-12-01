from .models import WatchList
from rest_framework import serializers
from utils.w3 import is_contract_address, to_checksum_address


class WatchListSerializer(serializers.ModelSerializer):
    """
    Serializer for the WatchList model.
    """

    telegram_user_id = serializers.CharField(
        error_messages={"required": "Telegram user id is required."}
    )

    class Meta:
        model = WatchList
        fields = ["telegram_user_id", "contract_address","percentage_change"]
        extra_kwargs = {
            "contract_address": {
                "error_messages": {"required": "Contract address is required."}
            }
        }

    def validate_contract_address(self, value):
        """
        Validate the contract address.
        """
        if not is_contract_address(value):
            raise serializers.ValidationError("Invalid contract address.")
        return to_checksum_address(value)


class WatchListGetSerializer(serializers.ModelSerializer):
    """
    Serializer for getting the watchlist.
    """

    class Meta:
        model = WatchList
        fields = ["uuid", "contract_address", "symbol"]


class SwapTokenSerializer(serializers.Serializer):
    """
    Serializer for swapping the token.
    """

    telegram_user_id = serializers.CharField(
        error_messages={"required": "Telegram user id is required."}
    )
    amount = serializers.FloatField(error_messages={"required": "Amount is required."})
    token_address = serializers.CharField(
        error_messages={"required": "Token address is required."}
    )
    swap_type = serializers.CharField(
        error_messages={"required": "Swap type is required."}
    )
    is_transfer = serializers.BooleanField(required=False, default=False)

    def validate_amount(self, value):
        """
        Validates the amount value.
        """
        if value <= 0:
            raise serializers.ValidationError("Amount should be greater than 0.")
        return value

    def validate_swap_type(self, value):
        """
        Validates the swap type value.
        """
        if value not in ["buy", "sell"]:
            raise serializers.ValidationError("Invalid swap type.")
        return value

    def validate_token_address(self, value):
        """
        Validates the token address value.
        """
        if value == "0xB8c77482e45F1F44dE1745F52C74426C631bDD52":
            raise serializers.ValidationError(
                "📉 Oops! This token isn’t traded on top U.S. exchanges. But don’t worry, you can still trade other ERC20 tokens! 🔍✨"
            )
        if len(value) != 42:
            raise serializers.ValidationError(
                "Token address should be of 42 characters."
            )
        if not is_contract_address(value):
            raise serializers.ValidationError("Invalid token address.")
        return value
