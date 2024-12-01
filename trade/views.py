import logging
import time
from django.conf import settings
from django.db import transaction
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .enums import TradeStatusChoices
from .models import CryptoTrade, Recifi
from .serializers import (
    CryptoTradeSerializer,
    recifierializer,
    CryptoTradeGetSerializer,
    Addrecifierializer,
)
from accounts.models import DefaultWallet, TelegramUser
from base.constants import WALLET_ADDRESS_REQ
from base.views import HandleException
from utils.covalent import (
    get_wallet_holdings,
    get_wallet_24h_percentage_change,
    get_wallet_1week_percentage_change,
    get_wallet_1month_percentage_change,
    get_wallet_1year_percentage_change,
)
from utils.encryption import decrypt_text
from utils.helper import send_buy_sell_notification
from utils.w3 import (
    check_balance_eth_usdt,
    sell_eth_for_usdt,
    buy_eth_from_usdt,
)


# Configure logging
logger = logging.getLogger(__name__)
logger_info = logging.getLogger("info")
logger_error = logging.getLogger("error")

# Create your views here.


class CryptoTradeView(HandleException, APIView):
    """
    API view to handle crypto trades.

    Methods: post: Handles the crypto trade process.
    """

    def get(self, request):
        """
        GET API to get the crypto trade details.
        """
        telegram_user_id = request.query_params.get("telegram_user_id")
        trade_status = request.query_params.get("status")

        if not telegram_user_id:
            logger_error.error("Telegram user ID is required.")
            return Response(
                {"status": False, "message": "Telegram user ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = dict(TradeStatusChoices).keys()

        if trade_status not in valid_statuses:
            return Response(
                {"status": False, "message": "Invalid status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        trades = CryptoTrade.objects.filter(
            telegram_user__telegram_user_id=telegram_user_id, status=trade_status
        )

        if not trades.exists():
            return Response(
                {"status": False, "message": "No trades found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CryptoTradeGetSerializer(trades, many=True)

        logger_info.info(f"Trade details fetched successfully for {telegram_user_id}.")
        return Response(
            {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
        )

    def post(self, request):
        logger_info.info("POST request to place a crypto trade.")
        """
        Handles the crypto buy-sell trade process.
        """
        data = request.data
        serializer = CryptoTradeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        telegram_user_id = serializer.validated_data["telegram_user_id"]
        trade_type = serializer.validated_data["trade_type"]
        quantity = serializer.validated_data["quantity"]
        target_price = serializer.validated_data["target_price"]
        logger_info.info(
            f"Telegram user ID: {telegram_user_id}, Trade Type: {trade_type}, Quantity: {quantity}, Target Price: {target_price}"
        )
        telegram_user = TelegramUser.objects.filter(
            telegram_user_id=telegram_user_id
        ).first()
        if not telegram_user:
            logger_info.info("Telegram user not found.")
            return Response(
                {"status": False, "message": "User does not exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        default_wallet = DefaultWallet.objects.filter(
            telegram_user=telegram_user
        ).first()
        if not default_wallet:
            logger_info.info("Default wallet not found.")
            return Response(
                {
                    "status": False,
                    "message": "Kindly set your default wallet to proceed with crypto trade.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        eth_balance, usdt_balance = check_balance_eth_usdt(
            address=default_wallet.user_wallet.wallet_address
        )
        if trade_type == "buy" and usdt_balance < quantity:
            return Response(
                {
                    "status": False,
                    "message": f"You wallet has {usdt_balance} USDT only.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if trade_type == "sell" and eth_balance < quantity:
            logger_info.info(f"Insufficient balance. ETH: {eth_balance}")
            return Response(
                {"status": False, "message": f"You wallet has {eth_balance} ETH only."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_trade = CryptoTrade.objects.filter(
            telegram_user=telegram_user,
            trade_type=trade_type,
            status="open",
        ).first()
        if existing_trade:
            existing_trade.quantity = quantity
            existing_trade.target_price = target_price
            existing_trade.save()
            logger_info.info("Trade updated successfully.")
            return Response(
                {
                    "status": True,
                    "message": "Your order has been successfully updated.",
                },
                status=status.HTTP_200_OK,
            )
        else:
            CryptoTrade.objects.create(
                telegram_user=telegram_user,
                user_wallet=default_wallet.user_wallet,
                trade_type=trade_type,
                quantity=quantity,
                target_price=target_price,
            )
            logger_info.info("Trade placed successfully.")
            return Response(
                {"status": True, "message": "Your order has been successfully placed."},
                status=status.HTTP_200_OK,
            )


class TradeDetailView(HandleException, APIView):
    """
    API view to cancel the trade.
    """

    # create a patch method to cancel the trade which takes uuid as a parameter
    def patch(self, request, uuid):
        """
        Cancels the trade based on the uuid.
        """
        logger_info.info(f"PATCH request to cancel the trade with UUID: {uuid}")
        with transaction.atomic():
            trade = (
                CryptoTrade.objects.select_for_update()
                .filter(uuid=uuid, status="open")
                .first()
            )
            if not trade:
                logger_error.error("Trade not found.")
                return Response(
                    {"status": False, "message": "Trade not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            trade.status = "cancelled"
            trade.save()
            logger_info.info("Trade cancelled successfully.")
            return Response(
                {"status": True, "message": "Trade cancelled successfully."},
                status=status.HTTP_200_OK,
            )


class ExecuteTrade(HandleException, APIView):
    """
    API view to execute the trade.
    """

    def post(self, request):
        """
        Executes the trade based on the close price.
        """
        data = request.data
        close_price = float(data.get("close_price"))
        with transaction.atomic():
            trades = CryptoTrade.objects.select_for_update(skip_locked=True).filter(
                status="open"
            )
            if not trades:
                return Response(
                    {"status": False, "message": "No open trades found."},
                    status=status.HTTP_200_OK,
                )
            for trade in trades:
                start_time = time.time()
                trade.status = "in_process"
                trade.save()
                private_key = decrypt_text(trade.user_wallet.private_key)
                execute_trade = None
                if trade.trade_type == "buy" and trade.target_price >= close_price:
                    logger_info.info(
                        f"Buying ETH from USDT. Close price: {close_price}"
                    )
                    execute_trade = buy_eth_from_usdt(
                        amount_eth=trade.quantity,
                        target_price=trade.target_price,
                        private_key=private_key,
                        current_price=close_price,
                    )
                elif trade.trade_type == "sell" and trade.target_price <= close_price:
                    logger_info.info(
                        f"Selling ETH for USDT. Close price: {close_price}"
                    )
                    execute_trade = sell_eth_for_usdt(
                        amount_eth=trade.quantity,
                        target_price=trade.target_price,
                        private_key=private_key,
                        current_price=close_price,
                    )
                else:
                    trade.status = "open"
                    trade.save()
                    continue

                if execute_trade and execute_trade[0]:
                    self.handle_successful_trade(
                        trade, execute_trade, close_price, start_time
                    )
                    return Response(
                        {"status": True, "message": "Trade executed successfully."},
                        status=status.HTTP_200_OK,
                    )
                else:
                    self.handle_failed_trade(trade, execute_trade)
                    return Response(
                        {"status": False, "message": "Trade execution failed."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        return Response(
            {"status": False, "message": "No trade executed."},
            status=status.HTTP_200_OK,
        )

    def handle_successful_trade(self, trade, execute_trade, close_price, start_time):
        trade.status = "closed"
        trade.save()
        trade_type = "bought" if trade.trade_type == "buy" else "sold"
        user = trade.telegram_user.telegram_user_id
        if trade.trade_type == "sell":
            message = (
                f"Hey user 👋, your transaction has been executed ✅. You can track status "
                f"of the transaction here on Etherscan 🔗{settings.TRANSACTION_HASH_URL}{execute_trade[1]}\n"
                f"{trade.quantity} ETH {trade_type} successfully at {close_price} price.🕵️‍♂️"
            )
        elif trade.trade_type == "buy":
            message = (
                f"Hey user 👋, your transaction has been executed ✅. You can track status "
                f"of the transaction here on Etherscan 🔗{settings.TRANSACTION_HASH_URL}{execute_trade[1]}\n"
                f"ETH {trade_type} successfully using {trade.quantity} USDT at {close_price} price."
            )
        else:
            message = ""
        send_buy_sell_notification(user, message)
        logger_info.info("Trade executed successfully.")
        end_time = time.time()
        logger_info.info(
            f"Trade executed successfully in {end_time - start_time} seconds."
        )

    def handle_failed_trade(self, trade, execute_trade):
        trade.status = "failed"
        trade.save()
        logger_info.info(
            f"Trade execution failed. {execute_trade[1] if execute_trade else 'Unknown error'}"
        )


class RecifiView(HandleException, generics.ListCreateAPIView):
    """
    API view to get Recifi whales.
    """

    def get_serializer_class(self):
        if self.request.method == "POST":
            return Addrecifierializer
        return recifierializer

    def get_queryset(self):
        """
        Get the top 5 Recifi objects based on percentage change.

        Excludes objects with no percentage change. If the 'type' query parameter
        is 'losers', returns the 5 objects with the lowest percentage change.
        Otherwise, returns the 5 objects with the highest percentage change.

        Returns:
            QuerySet: The top 5 Recifi objects.
        """
        logger_info.info(
            "GET request to get top 5 Recifi whales based on percentage change."
        )
        top_5_type = self.request.query_params.get("type")
        duration = self.request.query_params.get("duration")
        queryset = Recifi.objects.all()
        if top_5_type == "losers":
            if duration == "7d":
                queryset = queryset.order_by("pecentage_change_7days")[:5]
            elif duration == "1m":
                queryset = queryset.order_by("percentage_change_30days")[:5]
            elif duration == "1y":
                queryset = queryset.order_by("pecentage_change_1year")[:5]
            else:
                queryset = queryset.order_by("percentage_change_24hrs")[:5]
        else:
            if duration == "7d":
                queryset = queryset.order_by("-pecentage_change_7days")[:5]
            elif duration == "1m":
                queryset = queryset.order_by("-percentage_change_30days")[:5]
            elif duration == "1y":
                queryset = queryset.order_by("-pecentage_change_1year")[:5]
            else:
                queryset = queryset.order_by("-percentage_change_24hrs")[:5]

        logger_info.info("Recifi whales returned successfully.")
        return queryset

    def get_final_data(self, objs, duration):
        final_data = []
        duration_mapping = {
            "7d": "pecentage_change_7days",
            "1m": "percentage_change_30days",
            "1y": "pecentage_change_1year",
        }
        default_duration = "percentage_change_24hrs"
        for i in objs:
            percentage_change_key = duration_mapping.get(duration, default_duration)
            final_data.append(
                {
                    "name": i["name"],
                    "wallet_address": i["wallet_address"],
                    "percentage_change": i[percentage_change_key],
                }
            )
        return final_data

    def get(self, request, *args, **kwargs):
        """
        API view to get top 5 Recifi whales either losers or gainers based on perchange change.
        """
        logger_info.info("GET request to get top 5 Recifi whales.")
        data = super().get(self, request, *args, **kwargs)
        duration = self.request.query_params.get("duration")
        final_data = self.get_final_data(data.data, duration)
        logger_info.info("Recifi whales fetched successfully.")
        return Response({"status": True, "data": final_data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        API view to add Recifi whale wallet address to the "Recifi" model.
        """
        logger_info.info("POST request to add Recifi whale wallet address.")
        super().post(request, *args, **kwargs)
        return Response(
            {
                "status": True,
                "message": "Recifi whale wallet address added successfully.",
            },
            status=status.HTTP_200_OK,
        )


class RecifiWalletHoldings(HandleException, APIView):
    """
    API view to get Recifi whales wallet holdings.
    """

    def get(self, request):
        """
        API view to get wallet holdings of provided wallet address.
        """
        logger_info.info("GET request to get wallet holdings.")
        wallet_address = request.query_params.get("wallet_address")
        if not wallet_address:
            logger_error.error(WALLET_ADDRESS_REQ)
            return Response(
                {"status": False, "message": WALLET_ADDRESS_REQ},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Recifi_whale_wallet = Recifi.objects.filter(
            wallet_address=wallet_address
        ).first()
        if not Recifi_whale_wallet:
            logger_error.error(
                f"Provided wallet address {wallet_address} not found in our whale wallets list."
            )
            return Response(
                {
                    "status": False,
                    "message": "Provided wallet address not found in our whale wallets list.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        wallet_holdings = get_wallet_holdings(wallet_address)
        logger_info.info(f"Wallet holdings fetched successfully for {wallet_address}.")
        return Response(
            {"status": True, "data": wallet_holdings}, status=status.HTTP_200_OK
        )


class WalletPercentageChange(HandleException, APIView):
    """
    API view to get historical data of the wallet.
    """

    def get(self, request, wallet_address):
        """
        API view to get pecentage change of the wallet for the provided duration.
        """
        logger_info.info("GET request to get percentage change of the wallet.")
        duration = request.query_params.get("duration")
        if not duration:
            logger_error.error("Duration is required.")
            return Response(
                {"status": False, "message": "Duration is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if duration not in ["1d", "7d", "1m", "1y"]:
            logger_error.error("Invalid duration.")
            return Response(
                {"status": False, "message": "Invalid duration."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if duration == "1d":
            percentage_change = get_wallet_24h_percentage_change(wallet_address)
        elif duration == "7d":
            percentage_change = get_wallet_1week_percentage_change(wallet_address)
        elif duration == "1m":
            percentage_change = get_wallet_1month_percentage_change(wallet_address)
        elif duration == "1y":
            percentage_change = get_wallet_1year_percentage_change(wallet_address)
        else:
            percentage_change = None

        logger_info.info("Historical data fetched successfully.")
        return Response(
            {"status": True, "data": {"percentage_change": percentage_change}},
            status=status.HTTP_200_OK,
        )
