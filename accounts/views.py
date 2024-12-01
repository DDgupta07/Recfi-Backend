import logging
from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TelegramUser, UserWallet, DefaultWallet
from .serializers import (
    CreateWalletSerializer,
    UserWalletSeriallizer,
    ImportWalletSerializer,
    DefaultWalletSerializer,
    TransferTokenSerializer,
    VerifySellBotSerializer,
    DashboardSerializer,
    TokenBalanceSerializer,
    TransferTokenSerializer,
)
from base.constants import (
    TELEGRAM_USER_MESSAGE,
    DEFAULT_WALLET_MESSAGE,
    WALLET_NOT_FOUND,
    WALLET_NOT_BELONG,
)
from base.views import HandleException
from utils.covalent import fetch_covalent_data
from utils.encryption import encrypt_text, decrypt_text
from utils.helper import get_transaction_history
from utils.w3 import (
    create_wallet,
    import_wallet,
    transfer_token,
    check_balance_eth_usdt,
    get_token_balance,
    get_current_gwei,
    transfer_erc20_token,
)

# Configure logging
logger = logging.getLogger(__name__)
logger_info = logging.getLogger("info")
logger_error = logging.getLogger("error")


# Create your views here.


class CreateWallet(HandleException, APIView):
    """
    API view to create a new wallet for a Telegram user.

    Methods:
        post: Handles the creation of a new wallet.
    """

    def post(self, request):
        logger_info.info("Request recieved for create wallet API.")
        """
        Creates a new wallet for a Telegram user.
        """
        data = request.data
        serializer = CreateWalletSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        wallet_name = serializer.validated_data["wallet_name"]
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        logger_info.info(
            f"Received data for creating wallet: {wallet_name}, {telegram_user_id}"
        )
        telegram_user = TelegramUser.objects.filter(
            telegram_user_id=telegram_user_id
        ).first()
        if not telegram_user:
            logger_info.info(
                f"Creating new user with telegram user id {telegram_user_id}"
            )
            telegram_user = TelegramUser(telegram_user_id=telegram_user_id)
            telegram_user.save()
        wallet = create_wallet()
        UserWallet.objects.create(
            telegram_user=telegram_user,
            wallet_name=wallet_name,
            wallet_address=wallet["wallet_address"],
            private_key=encrypt_text(wallet["private_key"]),
        )
        logger_info.info(
            f"Wallet created for user {telegram_user_id}: {wallet['wallet_address']}"
        )
        return Response(
            {
                "status": True,
                "message": "Wallet created successfully.",
                "data": wallet,
            },
            status=status.HTTP_201_CREATED,
        )


class ImportWallet(HandleException, APIView):
    """
    API view to import an existing wallet for a Telegram user.

    Methods:
        post: Handles the import of an existing wallet (from other sources i.e. Metamask etc.).
    """

    def post(self, request):
        logger_info.info("Request recieved for import wallet API.")
        """
        Imports an existing wallet for a Telegram user.
        """
        data = request.data
        serializer = ImportWalletSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        private_key = serializer.validated_data["private_key"]
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        wallet_name = serializer.validated_data.get("wallet_name", None)
        logger_info.info(f"Importing wallet for user {telegram_user_id}")
        telegram_user = TelegramUser.objects.filter(
            telegram_user_id=telegram_user_id
        ).first()
        if not telegram_user:
            logger_info.info(
                f"Creating new user with telegram user id {telegram_user_id}"
            )
            telegram_user = TelegramUser(telegram_user_id=telegram_user_id)
            telegram_user.save()
        wallet = import_wallet(private_key)
        if not wallet_name:
            logger_info.info(f"Creating wallet name for user {telegram_user_id}")
            count = telegram_user.user_wallet.all().count()
            wallet_name = f"Account {count + 1}"

        if UserWallet.objects.filter(wallet_address=wallet).exists():
            logger_info.info(f"Wallet already imported for user {telegram_user_id}")
            return Response(
                {
                    "status": False,
                    "message": "This wallet has already been imported.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        UserWallet.objects.create(
            telegram_user=telegram_user,
            wallet_name=wallet_name,
            wallet_address=wallet,
            private_key=encrypt_text(private_key),
        )
        logger_info.info(f"Wallet imported for user {telegram_user_id}: {wallet}")
        return Response(
            {
                "status": True,
                "message": "Wallet imported successfully.",
                "data": {"wallet_address": wallet},
            },
            status=status.HTTP_201_CREATED,
        )


class UserWalletView(HandleException, generics.ListAPIView):
    """
    API view to list all wallets for a Telegram user.
    """

    serializer_class = UserWalletSeriallizer

    def get_queryset(self):
        logger_info.info("Request recieved for user wallet API.")
        """
        Retrieves the queryset of wallets for a Telegram user.

        Returns:
            QuerySet: The queryset of UserWallet objects.
        """
        telegram_user_id = self.request.query_params.get("telegram_user_id")
        logger_info.info(f"Retrieving wallets for user {telegram_user_id}")
        if telegram_user_id:
            queryset = UserWallet.objects.filter(
                telegram_user__telegram_user_id=telegram_user_id
            )
            logger_info.info(f"Wallets retrieved for user {telegram_user_id}")
            return queryset
        logger_info.info(f"No wallets found for user {telegram_user_id}")
        return None

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to list all wallets for a Telegram user.
        """
        logger_info.info("Retrieving wallets.")
        data = super().get(request, *args, **kwargs)
        logger_info.info("Wallets retrieved successfully.")
        return Response(
            {"status": True, "data": data.data},
            status=status.HTTP_200_OK,
        )


class WalletView(HandleException, APIView):
    """
    API view to retrieve, update, or delete a specific wallet.

    Methods:
        get_object: Retrieves a specific wallet by UUID.
        get: Retrieves wallet details.
        patch: Updates the wallet name.
        delete: Deletes the wallet.
    """

    def get_object(self, uuid):
        """
        Retrieves a specific wallet by UUID.

        Args:
            uuid (str): The UUID of the wallet.

        Returns:
            UserWallet: The UserWallet object.
        """
        logger_info.info(f"Request recieved for wallet API with UUID {uuid}")
        logger_info.info(f"Retrieving wallet with UUID {uuid}")
        return get_object_or_404(UserWallet, uuid=uuid)

    def get(self, request, uuid):
        """
        Retrieves wallet details.

        Args:
            uuid (str): The UUID of the wallet.

        Returns:
            Response: A response with the wallet details.
        """
        logger_info.info(f"Retrieving wallet with UUID {uuid}")
        wallet = self.get_object(uuid)
        serializer = UserWalletSeriallizer(wallet)
        logger_info.info(f"Wallet retrieved with UUID {uuid}")
        return Response(
            {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
        )

    def patch(self, request, uuid):
        """
        Updates the wallet name.

        Args:
            uuid (str): The UUID of the wallet.
        """
        logger_info.info(f"Request recieved for updating wallet name with UUID {uuid}")
        data = request.data
        wallet_name = data.get("wallet_name", None)
        logger_info.info(f"Updating wallet name for UUID {uuid}")
        if not wallet_name:
            logger_info.info("Wallet name is required.")
            return Response(
                {"status": False, "message": "Wallet name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        wallet = self.get_object(uuid)
        wallet.wallet_name = wallet_name
        wallet.save()
        logger_info.info(f"Wallet name updated for UUID {uuid} to {wallet_name}")
        return Response(
            {"status": True, "message": "Wallet renamed successfully."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, uuid):
        """
        Deletes the wallet.

        Args:
            uuid (str): The UUID of the wallet.
        """
        logger_info.info(f"Request recieved for deleting wallet with UUID {uuid}")
        obj = self.get_object(uuid)
        obj.soft_delete()
        default_wallet = DefaultWallet.objects.filter(user_wallet=obj).first()
        if default_wallet:
            default_wallet.delete()
        logger_info.info(f"Wallet deleted with UUID {uuid}")
        return Response(
            {"status": True, "message": "Wallet deleted successfully."},
            status=status.HTTP_200_OK,
        )


class DefaultWalletView(HandleException, APIView):
    """
    API view to manage a user's default wallet.

    Methods:
        get: Retrieves the default wallet details.
        post: Sets the default wallet.
    """

    def get(self, request):
        """
        Retrieves the default wallet details.
        """
        logger_info.info("Request recieved for default wallet API.")
        telegram_user_id = request.query_params.get("telegram_user_id")
        logger_info.info(f"Retrieving default wallet for user {telegram_user_id}")
        if not telegram_user_id:
            logger_error.error("Telegram user id is not provided.")
            return Response(
                {"status": False, "message": TELEGRAM_USER_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )
        default_wallet = DefaultWallet.objects.filter(
            telegram_user__telegram_user_id=telegram_user_id
        ).first()
        if not default_wallet:
            logger_error.error(DEFAULT_WALLET_MESSAGE)
            return Response(
                {
                    "status": False,
                    "message": "The default wallet has not been configured.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserWalletSeriallizer(default_wallet.user_wallet)
        logger_info.info(f"Default wallet retrieved for user {telegram_user_id}")
        return Response(
            {"status": True, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Sets the default wallet.
        """
        logger_info.info("Request recieved for setting default wallet API.")
        data = request.data
        serializer = DefaultWalletSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        wallet = serializer.validated_data["user_wallet"]
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        telegram_user = TelegramUser.objects.get(telegram_user_id=telegram_user_id)
        logger_info.info(f"Setting default wallet for user {telegram_user_id}")
        user_wallet = UserWallet.objects.filter(
            uuid=wallet.uuid, telegram_user=telegram_user
        ).first()
        if not user_wallet:
            logger_info.info("Wallet does not belong to user.")
            return Response(
                {"status": False, "message": "This wallet does not belongs to you."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        default_wallet = DefaultWallet.objects.filter(
            telegram_user=telegram_user
        ).first()
        if default_wallet:
            default_wallet.user_wallet = wallet
            default_wallet.save()
        else:
            serializer.validated_data.pop("telegram_user_id", None)
            serializer.validated_data["telegram_user"] = telegram_user
            serializer.save()
        logger_info.info(f"Default wallet set for user {telegram_user_id}")
        return Response(
            {"status": True, "message": "Default wallet set successfully."},
            status=status.HTTP_200_OK,
        )


class TransferToken(HandleException, APIView):
    """
    API view to handle token transfers.

    Methods:
        post: Handles the token transfer process.
    """

    def post(self, request):
        """
        Handles the token transfer process.
        """
        logger_info.info("Request recieved for token transfer API.")
        data = request.data
        serializer = TransferTokenSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        wallet_address = serializer.validated_data.get("wallet_address", None)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        logger_info.info(f"Transferring token for user {telegram_user_id}")
        telegram_user = TelegramUser.objects.filter(
            telegram_user_id=telegram_user_id
        ).first()
        if not telegram_user:
            logger_info.info("User not exist.")
            return Response(
                {"status": False, "message": "User does not exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if wallet_address:
            wallet = UserWallet.objects.filter(
                telegram_user__telegram_user_id=telegram_user_id,
                wallet_address=wallet_address,
            ).first()
            if not wallet:
                logger_info.info("Not provided correct wallet address.")
                return Response(
                    {
                        "status": False,
                        "message": "Kindly provide your correct wallet address.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            wallet_address = wallet.wallet_address
            private_key = wallet.private_key
        else:
            default_wallet = DefaultWallet.objects.filter(
                telegram_user=telegram_user
            ).first()
            if default_wallet:
                wallet_address = default_wallet.user_wallet.wallet_address
                private_key = default_wallet.user_wallet.private_key
            else:
                user_wallets = UserWallet.objects.filter(
                    telegram_user__telegram_user_id=telegram_user_id
                )
                if not user_wallets:
                    logger_info.info("User has not created any wallet.")
                    return Response(
                        {
                            "status": False,
                            "message": "You have still not created any wallet.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if user_wallets.count() > 1:
                    logger_info.info(
                        "Kindly provide wallet address for token transfer."
                    )
                    return Response(
                        {
                            "status": False,
                            "message": "Kindly provide wallet address for token transfer.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                wallet = user_wallets.first()
                wallet_address = wallet.wallet_address
                private_key = wallet.private_key

        amount = Decimal(str(serializer.validated_data["amount"]))
        receiver_address = serializer.validated_data["receiver_address"]
        logger_info.info(
            f"Transferring {amount} tokens from {wallet_address} to {receiver_address}"
        )
        transfer_token(
            private_key=decrypt_text(private_key),
            wallet_address=wallet_address,
            receiver_address=receiver_address,
            amount=amount,
        )
        logger_info.info(
            f"Token transffered successfully to {receiver_address} wallet address."
        )
        return Response(
            {
                "status": True,
                "message": f"Token transffered successfully to {receiver_address} wallet address.",
            },
            status=status.HTTP_200_OK,
        )


class TransferErc20Token(HandleException, APIView):
    """
    API view to handle ERC-20 token transfers.

    Methods:
        post: Handles the ERC-20 token transfer process.
    """

    def post(self, request):
        """
        Handles the ERC-20 token transfer process.
        """
        logger_info.info("Request received for ERC-20 token transfer API.")
        data = request.data
        serializer = TransferTokenSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        wallet_address = serializer.validated_data.get("wallet_address", None)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        logger_info.info(f"Transferring ERC-20 token for user {telegram_user_id}")
        telegram_user = TelegramUser.objects.filter(
            telegram_user_id=telegram_user_id
        ).first()
        if not telegram_user:
            logger_info.info("User does not exist")
            return Response(
                {"status": False, "message": "User does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if wallet_address:
            wallet = UserWallet.objects.filter(
                telegram_user__telegram_user_id=telegram_user_id,
                wallet_address=wallet_address,
            ).first()

            if not wallet:
                logger_info.info("Not provided correct wallet address.")
                return Response(
                    {
                        "status": False,
                        "message": "Kindly provide your correct wallet address.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            private_key = wallet.private_key

        else:
            wallet = DefaultWallet.objects.filter(telegram_user=telegram_user).first()
            if not wallet:
                logger_info.info("Default wallet not set.")
                return Response(
                    {
                        "status": False,
                        "message": "Kindly set your default wallet to proceed.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            wallet_address = wallet.user_wallet.wallet_address
            private_key = wallet.user_wallet.private_key

        amount = serializer.validated_data["amount"]
        receiver_address = serializer.validated_data["receiver_address"]
        token_address = serializer.validated_data["token_address"]
        logger_info.info(
            f"Transferring {amount} ERC-20 tokens from {wallet_address} to {receiver_address}"
        )
        tx_hash = transfer_erc20_token(
            private_key=decrypt_text(private_key),
            wallet_address=wallet_address,
            receiver_address=receiver_address,
            amount=amount,
            token_address=token_address,
        )
        logger_info.info(
            f"Token transferred successfully to {receiver_address} wallet address, transaction hash: {tx_hash}"
        )
        return Response(
            {
                "status": True,
                "message": f"Token transferred successfully to {receiver_address} wallet address.",
                "data": {
                    "tx_hash": tx_hash,
                    "tx_url": f"{settings.TRANSACTION_HASH_URL}{tx_hash}",
                },
            },
            status=status.HTTP_200_OK,
        )


class SellBotVerification(HandleException, APIView):
    """
    API view to verify the sell bot.
    """

    def post(self, request):
        """
        Handles the private key verification process.
        """
        logger_info.info("Request recieved for sell bot verification API.")
        serializer = VerifySellBotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        telegram_user_id = serializer.validated_data["telegram_user_id"]
        private_key = serializer.validated_data.get("private_key", None)
        logger_info.info(f"Verifying sell bot for user {telegram_user_id}")

        telegram_user = TelegramUser.objects.filter(
            telegram_user_id=telegram_user_id
        ).first()

        if not telegram_user:
            logger_info.info("User does not exist.")
            return Response(
                {"status": False, "message": "User does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        default_wallet = DefaultWallet.objects.filter(
            telegram_user=telegram_user
        ).first()

        if not default_wallet:
            logger_error.error(DEFAULT_WALLET_MESSAGE)
            return Response(
                {
                    "status": False,
                    "message": "Kindly set your default wallet to proceed with sell bot.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user is already verified
        if default_wallet.user_wallet.is_verified:
            logger_info.info("User's default wallet is already verified.")
            return Response(
                {"status": True, "message": "Your default wallet is already verified."},
                status=status.HTTP_200_OK,
            )

        if not private_key:
            logger_info.info("Private key is required.")
            return Response(
                {
                    "status": False,
                    "message": "Kindly provide private key of your default wallet.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_private_key = decrypt_text(default_wallet.user_wallet.private_key)
        if user_private_key != private_key:
            logger_info.info("Private key not provided.")
            return Response(
                {
                    "status": False,
                    "message": "Kindly provide private key of your default wallet.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        default_wallet.user_wallet.is_verified = True
        default_wallet.user_wallet.save()
        logger_info.info("Verification successful.")
        return Response(
            {"status": True, "message": "Verification successful."},
            status=status.HTTP_200_OK,
        )


class TransactionHistory(HandleException, APIView):
    """
    API view to get transaction history of a wallet.
    """

    def post(self, request):
        """
        Get transaction history of a wallet.
        """
        logger_info.info("Request recieved for transaction history API.")
        data = request.data
        serializer = DashboardSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        wallet_address = serializer.validated_data["wallet_address"]
        logger_info.info(
            f"Retrieving transaction history data for user {telegram_user_id} and wallet {wallet_address}"
        )
        user_wallet = UserWallet.objects.filter(
            telegram_user__telegram_user_id=telegram_user_id,
            wallet_address=wallet_address,
        ).first()
        if not user_wallet:
            logger_error.error(WALLET_NOT_FOUND)
            return Response(
                {"status": False, "message": WALLET_NOT_BELONG},
                status=status.HTTP_400_BAD_REQUEST,
            )
        transactions = get_transaction_history(wallet_address)
        logger_info.info(f"Transaction history retrieved for wallet {wallet_address}")
        return Response(
            {"status": True, "data": transactions}, status=status.HTTP_200_OK
        )


class TokenHoldingView(HandleException, APIView):
    """
    API view to get token holding of a wallet.
    """

    def post(self, request):
        logger_info.info("Request recieved for token holding API.")
        data = request.data
        telegram_user_id = data.get("telegram_user_id", None)
        wallet_address = data.get("wallet_address", None)
        if not telegram_user_id:
            logger_info.info(TELEGRAM_USER_MESSAGE)
            return Response(
                {"status": False, "message": TELEGRAM_USER_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if wallet_address:
            user_wallet = UserWallet.objects.filter(
                telegram_user__telegram_user_id=telegram_user_id,
                wallet_address=wallet_address,
            ).first()
            if not user_wallet:
                logger_error.error(WALLET_NOT_FOUND)
                return Response(
                    {"status": False, "message": WALLET_NOT_BELONG},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if not wallet_address:
            default_wallet = DefaultWallet.objects.filter(
                telegram_user__telegram_user_id=telegram_user_id
            ).first()
            if not default_wallet:
                logger_error.error(DEFAULT_WALLET_MESSAGE)
                return Response(
                    {
                        "status": False,
                        "message": "Kindly set your default wallet to proceed or provide wallet address.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            wallet_address = default_wallet.user_wallet.wallet_address
        logger_info.info(
            f"Retrieving token holding data for user {telegram_user_id} and wallet {wallet_address}"
        )
        logger_info.info(f"Token holding data retrieved for wallet {wallet_address}")
        tokens = fetch_covalent_data(wallet_address)
        token_holdings = {
            "eth_balance": 0,
            "token_holdings": [],
        }
        for token in tokens:
            balance = float(token["balance"]) / (10 ** token["contract_decimals"])
            if token["contract_ticker_symbol"] == "ETH":
                token_holdings["eth_balance"] = balance
            else:
                holding = {
                    "name": token["contract_name"],
                    "balance": balance,
                }
                token_holdings["token_holdings"].append(holding)
        return Response(
            {"status": True, "data": token_holdings}, status=status.HTTP_200_OK
        )


class EthUsdtBalance(HandleException, APIView):
    """
    API view to get balance of a wallet.
    """

    def post(self, request):
        logger_info.info("Request recieved for Eth-Usdt balance API.")
        data = request.data
        telegram_user_id = data.get("telegram_user_id", None)
        wallet_address = data.get("wallet_address", None)
        if not telegram_user_id:
            logger_info.info(TELEGRAM_USER_MESSAGE)
            return Response(
                {"status": False, "message": TELEGRAM_USER_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if wallet_address:
            user_wallet = UserWallet.objects.filter(
                telegram_user__telegram_user_id=telegram_user_id,
                wallet_address=wallet_address,
            ).first()
            if not user_wallet:
                logger_error.error(WALLET_NOT_FOUND)
                return Response(
                    {"status": False, "message": WALLET_NOT_BELONG},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if not wallet_address:
            default_wallet = DefaultWallet.objects.filter(
                telegram_user__telegram_user_id=telegram_user_id
            ).first()
            if not default_wallet:
                logger_error.error(DEFAULT_WALLET_MESSAGE)
                return Response(
                    {
                        "status": False,
                        "message": "Kindly set your default wallet to proceed or provide wallet address.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            wallet_address = default_wallet.user_wallet.wallet_address
        logger_info.info(
            f"Retrieving balance data for user {telegram_user_id} and wallet {wallet_address}"
        )
        eth, usdt = check_balance_eth_usdt(wallet_address)
        balance = {"eth": eth, "usdt": usdt}
        logger_info.info(f"Balance data retrieved for wallet {wallet_address}")
        return Response({"status": True, "data": balance}, status=status.HTTP_200_OK)


class TokenBalanceView(HandleException, APIView):
    """
    API view to get balance of a token.
    """

    def post(self, request):
        """
        Handle POST request to get the balance of a token.

        Returns:
            Response: A response containing the status and the balance along with the token name.
        """

        logger_info.info("Request recieved for token balance API.")
        data = request.data
        serializer = TokenBalanceSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        default_wallet = DefaultWallet.objects.filter(
            telegram_user__telegram_user_id=telegram_user_id
        ).first()
        if not default_wallet:
            logger_error.error(DEFAULT_WALLET_MESSAGE)
            return Response(
                {
                    "status": False,
                    "message": "Kindly set your default wallet to proceed.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        wallet_address = default_wallet.user_wallet.wallet_address
        token_address = serializer.validated_data["token_address"]
        name, balance = get_token_balance(token_address, wallet_address)
        logger_info.info(
            f"Retrieving token balance data for user {telegram_user_id} and wallet {wallet_address}"
        )
        return Response(
            {
                "status": True,
                "data": {"token_name": name, "balance": balance},
            },
            status=status.HTTP_200_OK,
        )


class CurrentGweiView(HandleException, APIView):
    """
    API view to get the current Gwei value.
    """

    def get(self, request):
        """
        Handle GET request to get the current Gwei value.

        Returns:
            Response: A response containing the status and the current Gwei value.
        """
        logger_info.info("Request recieved for current Gwei API.")
        gwei = get_current_gwei()
        logger_info.info(f"Current Gwei value: {gwei}")
        return Response(
            {"status": True, "data": {"gwei": gwei}},
            status=status.HTTP_200_OK,
        )
