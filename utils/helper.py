import logging
import requests
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from django.conf import settings

from pulse_tracker.models import WatchList
from accounts.models import TelegramUser

logger = logging.getLogger(__name__)
logger_info = logging.getLogger("info")
logger_error = logging.getLogger("error")


def send_buy_sell_notification(user, message):
    """
    Send a notification to a user.
    """
    token = settings.BUY_SELL_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": user,
        "text": message,
    }
    response = requests.post(url, json=data)
    logger_info.info(f"Notification for user {user} : {response.json()}")
    return True if response.status_code == 200 else False


def send_pulse_tracker_notification(user, message, notification_data):
    """
    Send a notification to the pulse tracker bot.
    """
    symbol = notification_data["symbol"]
    token_address = notification_data["token_address"]
    percentage = notification_data["percentage"]
    url = f"https://api.telegram.org/bot{settings.PULSE_TRACKER_BOT_TOKEN}/sendMessage"
    bot_link = (
        f"https://t.me/RecifiAi_sell_bot?start={symbol}_{token_address}_{percentage}"
    )
    data = {
        "chat_id": user,
        "text": message,
        "reply_markup": {"inline_keyboard": [[{"text": "Buy/Sell", "url": bot_link}]]},
    }
    response = requests.post(url, json=data)
    logger_info.info(f"Notification for user {user} : {response.json()}")
    return True if response.status_code == 200 else False


def send_Recifi_alert_notification(notification_data):
    """
    Send a notification to the Recifi alert bot.
    """
    symbol = notification_data["symbol"]
    token_address = notification_data["token_address"]
    percentage = notification_data["percentage"]
    url = (
        f"https://api.telegram.org/bot{settings.Recifi_ALERT_BOT_TOKEN}/sendMessage"
    )
    bot_link = "https://t.me/RecifiAi_sell_bot"

    message = (
        f"🚨 Whale Movement Alert! 🚨\n"
        f"🐋 {percentage}% whale wallets have just bought {symbol}!\n"
        f"📜 Contract Address: {token_address}\n"
        f"🔍 Check it out on [Etherscan]({settings.ETHERSCAN_URL}{token_address}) "
        f"or [DEXTOOLS]({settings.DEXTOOLS_URL}{token_address})!"
    )

    users = TelegramUser.objects.all()
    for user in users:
        data = {
            "chat_id": user.telegram_user_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard": [[{"text": "Buy", "url": bot_link}]]},
        }

        try:
            response = requests.post(url, json=data)
            logger_info.info(
                f"Notification sent to user {user.telegram_user_id}: {response.json()}"
            )
        except requests.exceptions.RequestException as e:
            logger_info.error(
                f"Failed to send notification to user {user.telegram_user_id}: {e}"
            )


def get_watchlist_symbols():
    """
    Get the list of crypto symbols
    """
    symbols = WatchList.objects.all().values_list("symbol", flat=True).distinct()
    return list(symbols)


def get_percentage_change():
    """
    Get the percentage change of the crypto symbols
    """
    start = time.time()
    symbols = get_watchlist_symbols()
    binance_url = f"{settings.BINANCE_API}"
    for symbol in symbols:
        params = {"symbol": f"{symbol}USDT"}
        response = requests.get(binance_url, params=params)

        if response.status_code == 200:
            data = response.json()
            price_change_percent = float(data["priceChangePercent"])
            url = f"{settings.BACKEND_URL}/api/notify/"
            data = {"symbol": symbol, "percentage": price_change_percent}
            logger_info.info(f"Sending notification for {symbol} : {data}")
            requests.post(url, data)
    end = time.time()
    return f"Time taken to compelete pulse-tracker notification: {end - start} seconds."


def get_transaction_history(wallet_address):
    """
    Get the transaction history for a wallet address.
    """
    etherscan_url = settings.ETHERSCAN_API_URL
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": settings.ETHERSCAN_API_KEY,
    }
    response = requests.get(etherscan_url, params=params)
    response.raise_for_status()
    data = response.json()
    if data["status"] == "1":
        transactions = data["result"][::-1][:10]
        response_data = []
        for transaction in transactions:
            tx_hash_url = f"{settings.TRANSACTION_HASH_URL}{transaction['hash']}"
            response_data.append({"tx_hash_url": tx_hash_url})
        return response_data
    else:
        logger_error.error(f"Etherscan API error: {data['message']}")
        return []


def calculate_percent_change(current_value, previous_value):
    if previous_value != 0 and current_value and previous_value:
        percent_change = ((current_value - previous_value) / previous_value) * 100
        return Decimal(percent_change).quantize(Decimal("0.00"))
    else:
        return Decimal(0)


def get_bought_token(wallet_address, minutes=60):
    """
    Get the transaction history for a wallet address and filter transactions within the specified minutes.
    """
    logger_info.info(
        f"Fetching Recifi bought token addresses for wallet {wallet_address}."
    )
    params = {
        "module": "account",
        "action": "tokentx",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": settings.ETHERSCAN_API_KEY,
    }
    response = requests.get(settings.ETHERSCAN_API_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if data["status"] == "1":
        transactions = data["result"]
        bought_token_addresses = []
        now = datetime.now(timezone.utc)

        # Filter transactions based on the minutes parameter
        if minutes is not None:
            cutoff_time = now - timedelta(minutes=minutes)
            transactions = [
                tx
                for tx in transactions
                if datetime.fromtimestamp(int(tx["timeStamp"]), timezone.utc)
                >= cutoff_time
            ]

        # Extract bought token addresses
        for transaction in transactions:
            if transaction["to"].lower() == wallet_address.lower():
                bought_token_addresses.append(transaction["contractAddress"])

        bought_token_addresses = list(set(bought_token_addresses))
        return bought_token_addresses
    else:
        return []


def sum_all_quote(data):
    total_sum = 0
    for i in data:
        quote = i.get("quote")
        if quote is not None:
            total_sum += Decimal(str(quote))
    return total_sum
