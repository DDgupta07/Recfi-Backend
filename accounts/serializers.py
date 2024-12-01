from rest_framework import serializers

from .models import UserWallet, DefaultWallet
from utils.w3 import is_contract_address

ERROR_MESSAGE = "Telegram user id is required."


class CreateWalletSerializer(serializers.Serializer):
    """
    Serializer for creating a new wallet.
    """

    telegram_user_id = serializers.CharField(error_messages={"required": ERROR_MESSAGE})
    wallet_name = serializers.CharField(
        error_messages={"required": "Wallet name is required."}
    )


class ImportWalletSerializer(serializers.Serializer):
    """
    Serializer for importing a wallet.
    """

    telegram_user_id = serializers.CharField(error_messages={"required": ERROR_MESSAGE})
    private_key = serializers.CharField(
        error_messages={"required": "Private key is required."}
    )
    wallet_name = serializers.CharField(required=False)


class UserWalletSeriallizer(serializers.ModelSerializer):
    """
    Serializer for the UserWallet model.
    """

    etherscan_url = serializers.ReadOnlyField(source="get_etherscan_url")
    balance = serializers.ReadOnlyField(source="get_balance")
    is_default = serializers.SerializerMethodField()

    class Meta:
        model = UserWallet
        fields = [
            "uuid",
            "wallet_name",
            "wallet_address",
            "etherscan_url",
            "balance",
            "is_default",
        ]

    def get_is_default(self, obj):
        """
        Returns True if the wallet is the default wallet for the user, else False.
        """
        try:
            default_wallet = DefaultWallet.objects.get(telegram_user=obj.telegram_user)
            return obj == default_wallet.user_wallet
        except DefaultWallet.DoesNotExist:
            return False


class DefaultWalletSerializer(serializers.ModelSerializer):
    """
    Serializer for the DefaultWallet model.
    """

    telegram_user_id = serializers.CharField(error_messages={"required": ERROR_MESSAGE})

    class Meta:
        model = DefaultWallet
        exclude = ["telegram_user"]
        extra_kwargs = {
            "user_wallet": {
                "error_messages": {"required": "Kindly provide wallet uuid."}
            },
        }


class TransferTokenSerializer(serializers.Serializer):
    """
    Serializer for transferring tokens.
    """

    telegram_user_id = serializers.CharField(error_messages={"required": ERROR_MESSAGE})
    amount = serializers.FloatField(
        error_messages={"required": "Kindly provide amount to transfer."}
    )
    receiver_address = serializers.CharField(
        error_messages={
            "required": "Kindly provide receiver address for token transfer."
        }
    )
    wallet_address = serializers.CharField(
        required=False,
        error_messages={
            "required": "Kindly provide wallet address for token transfer."
        },
    )


from rest_framework import serializers


class TransferTokenSerializer(serializers.Serializer):
    wallet_address = serializers.CharField(
        required=False,
        error_messages={
            "required": "Kindly provide wallet address for token transfer."
        },
    )
    telegram_user_id = serializers.CharField(error_messages={"required": ERROR_MESSAGE})
    amount = serializers.DecimalField(
        max_digits=100,
        decimal_places=2,
        error_messages={"required": "Kindly provide amount to transfer."},
    )
    receiver_address = serializers.CharField(
        error_messages={
            "required": "Kindly provide receiver address for token transfer."
        }
    )
    token_address = serializers.CharField(
        error_messages={"required": "Token address is required."}
    )

    def validate_token_address(self, value):
        """
        Validates the token address value.
        """
        if len(value) != 42:
            raise serializers.ValidationError(
                "Token address should be of 42 characters."
            )
        if not is_contract_address(value):
            raise serializers.ValidationError("Invalid token address.")
        return value

    def validate_wallet_address(self, value):
        """
        Validates the wallet address value.
        """
        if len(value) != 42:
            raise serializers.ValidationError(
                "Wallet address should be of 42 characters."
            )
        return value

    def validate_receiver_address(self, value):
        """
        Validates the receiver address value.
        """
        if len(value) != 42:
            raise serializers.ValidationError(
                "Receiver address should be of 42 characters."
            )
        return value

    def validate_amount(self, value):
        """
        Validates the amount value.
        """
        if value <= 0:
            raise serializers.ValidationError("Amount should be greater than 0.")
        return value


class VerifySellBotSerializer(serializers.Serializer):
    telegram_user_id = serializers.CharField(error_messages={"required": ERROR_MESSAGE})
    private_key = serializers.CharField(required=False)

    def validate_private_key(self, private_key):
        """
        Validates the private key.

        Args:
            value (str): Private key to validate.

        Returns:
            str: Private key.
        """
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        if len(private_key) != 64:
            raise serializers.ValidationError("Invalid private key.")
        private_key = f"0x{private_key}"
        return private_key


class DashboardSerializer(serializers.Serializer):
    """
    Serializer for the dashboard.
    """

    telegram_user_id = serializers.CharField(error_messages={"required": ERROR_MESSAGE})
    wallet_address = serializers.CharField(
        error_messages={"required": "Kindly provide wallet address."}
    )


class TokenBalanceSerializer(serializers.Serializer):
    """
    Serializer for the token balance.

    Validates the input data for the token balance API, ensuring that both
    the telegram_user_id and token_address are provided.
    """

    telegram_user_id = serializers.CharField(error_messages={"required": ERROR_MESSAGE})
    token_address = serializers.CharField(
        error_messages={"required": "Token address is required."}
    )

    def validate_token_address(self, value):
        """
        Validates the token address value.
        """
        if len(value) != 42:
            raise serializers.ValidationError(
                "Token address should be of 42 characters."
            )
        if not is_contract_address(value):
            raise serializers.ValidationError("Invalid token address.")
        return value
