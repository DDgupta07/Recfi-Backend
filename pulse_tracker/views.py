import logging
import time
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WatchList
from .serializers import (
    WatchListSerializer,
    WatchListGetSerializer,
    SwapTokenSerializer,
)
from accounts.models import TelegramUser, DefaultWallet
from base.views import HandleException
from utils.encryption import decrypt_text
from utils.w3 import get_token_symbol, swap_eth_to_token, swap_token_to_eth
from utils.helper import send_pulse_tracker_notification


# Configure logging
logger = logging.getLogger(__name__)
logger_info = logging.getLogger("info")
logger_error = logging.getLogger("error")

TELEGRAM_USER_ERROR_MSG = "Telegram user not found."


class WatchListView(HandleException, APIView):
    """
    API view for handling WatchList operations like GET and POST.
    """

    def get(self, request):
        """
        Get method to fetch all watchlist entries for a specified Telegram user.
        """
        logger_info.info("GET request to fetch watchlist entries.")
        telegram_user_id = request.query_params.get("telegram_user_id")
        objs = WatchList.objects.filter(
            telegram_user__telegram_user_id=telegram_user_id
        )
        serializer = WatchListGetSerializer(objs, many=True)
        logger_info.info("Watchlist entries fetched successfully.")
        return Response(
            {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
        )

    def post(self, request):
        """
        Post method to add a new entry to the watchlist.
        """
        logger_info.info("POST request to add a new entry to the watchlist.")
        data = request.data
        serializer = WatchListSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        logger_info.info(f"Telegram user ID: {telegram_user_id}")
        user_obj = TelegramUser.objects.filter(
            telegram_user_id=telegram_user_id
        ).first()
        if not user_obj:
            logger_info.info(TELEGRAM_USER_ERROR_MSG)
            return Response(
                {"status": False, "message": TELEGRAM_USER_ERROR_MSG},
                status=status.HTTP_400_BAD_REQUEST,
            )
        contract_address = serializer.validated_data["contract_address"]
        watch_list_obj = WatchList.objects.filter(
            telegram_user=user_obj, contract_address=contract_address
        ).first()
        if watch_list_obj:
            logger_info.info(
                "Provided contract address already in watchlist for the user."
            )
            return Response(
                {
                    "status": False,
                    "message": "Provided contract address already exists in your watchlist.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        percentage_change = serializer.validated_data["percentage_change"]
        symbol = get_token_symbol(contract_address)
        WatchList.objects.create(
            telegram_user=user_obj, contract_address=contract_address, symbol=symbol, percentage_change= percentage_change
        )
        logger_info.info("Watchlist added successfully.")
        return Response(
            {
                "status": True,
                "message": "Watchlist added successfully.",
                "data": {"symbol": symbol},
            },
            status=status.HTTP_201_CREATED,
        )


class WatchListDetail(HandleException, APIView):
    """
    API view to handle Pulse Tracker operations.
    """

    def delete(self, request, uuid):
        """
        Delete method to remove an entry from the watchlist.
        """
        logger_info.info("DELETE request to remove an entry from the watchlist.")
        watchlist_obj = WatchList.objects.filter(uuid=uuid).first()
        if not watchlist_obj:
            logger_info.info("Watchlist entry not found.")
            return Response(
                {"status": False, "message": "Watchlist entry not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        watchlist_obj.delete()
        logger_info.info("Watchlist entry removed successfully.")
        return Response(
            {"status": True, "message": "Watchlist entry removed successfully."},
            status=status.HTTP_200_OK,
        )


class PulseTrackerNotification(HandleException, APIView):
    """
    API view to handle sending notifications based on token price changes.
    """

    def post(self, request):
        logger_info.info(
            "POST request to send notifications based on token price changes."
        )
        data = request.data
        symbol = data.get("symbol").upper()
        percentage = float(data.get("percentage"))
        notification_data = {"symbol": symbol, "percentage": percentage}
        logger_info.info(f"Symbol: {symbol}, Percentage: {percentage}")
        watchlists = WatchList.objects.filter(symbol=symbol)
        for watchlist in watchlists:
            user = watchlist.telegram_user.telegram_user_id
            percentage_change = watchlist.percentage_change
            logger_info.info(percentage_change)
            if percentage>=percentage_change or percentage<=-percentage_change:
                message = f"🎉 Congratulations! Your token {symbol} has increased by {percentage}%! 📈 If you would like to buy or sell, please proceed. 💰"
                logger_info.info(message)
                notification_data["token_address"] = watchlist.contract_address
                send_pulse_tracker_notification(user, message, notification_data)
        return Response(
            {"status": True, "message": "Notification sent successfully."},
            status=status.HTTP_200_OK,
        )


class SwapTokenView(HandleException, APIView):
    """
    API view to handle token swap operations.
    """

    def post(self, request):
        start_time = time.time()
        logger_info.info("POST request to swap tokens.")
        data = request.data
        serializer = SwapTokenSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        is_transfer = serializer.validated_data["is_transfer"]
        logger_info.info(f"Telegram user ID: {telegram_user_id}")
        user_obj = TelegramUser.objects.filter(
            telegram_user_id=telegram_user_id
        ).first()
        if not user_obj:
            logger_info.info(TELEGRAM_USER_ERROR_MSG)
            return Response(
                {"status": False, "message": TELEGRAM_USER_ERROR_MSG},
                status=status.HTTP_400_BAD_REQUEST,
            )
        amount = serializer.validated_data["amount"]
        token_address = serializer.validated_data["token_address"]
        swap_type = serializer.validated_data["swap_type"]
        logger_info.info(
            f"Amount: {amount}, Token Address: {token_address}, Swap Type: {swap_type}"
        )
        default_wallet = DefaultWallet.objects.filter(telegram_user=user_obj).first()
        if not default_wallet:
            logger_info.info("Default wallet not found.")
            return Response(
                {"status": False, "message": "Default wallet not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        private_key = decrypt_text(default_wallet.user_wallet.private_key)
        if swap_type == "buy":
            logger_info.info("Swapping ETH to token.")
            tx = swap_eth_to_token(private_key, amount, token_address, is_transfer)
        elif swap_type == "sell":
            logger_info.info("Swapping token to ETH.")
            tx = swap_token_to_eth(private_key, amount, token_address, is_transfer)
        else:
            logger_info.info("Invalid swap type.")
            return Response(
                {"status": False, "message": "Invalid swap type."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tx_url = f"{settings.TRANSACTION_HASH_URL}{tx}"
        logger_info.info(f"Transaction URL: {tx_url}")
        end_time = time.time()
        logger_info.info(
            f"Time taken to complete the transaction: {end_time - start_time} seconds"
        )
        return Response(
            {
                "status": True,
                "message": f"You can view your transaction status at {tx_url}",
                "data": {"tx_url": tx_url},
            },
            status=status.HTTP_200_OK,
        )
