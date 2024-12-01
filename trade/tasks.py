import time
import logging
from celery import shared_task

from .models import Recifi, RecifiToken
from utils.covalent import (
    get_wallet_24h_percentage_change,
    get_bought_token,
    get_wallet_price_change,
)
from utils.helper import send_Recifi_alert_notification, calculate_percent_change
from utils.w3 import get_token_symbol, to_checksum_address

logger = logging.getLogger(__name__)
logger_info = logging.getLogger("info_logger")
logger_error = logging.getLogger("error_logger")


@shared_task()
def Recifi_wallets_24h_percentage_change():
    """
    Updates the percentage change for each wallet in the Recifi model at every 24hrs.
    """
    start_time = time.time()
    objs = Recifi.objects.all()
    for obj in objs:
        percentage_24hrs_change, total_holdings = get_wallet_24h_percentage_change(
            obj.wallet_address
        )
        obj.percentage_change_24hrs = percentage_24hrs_change
        obj.pecentage_change_7days = calculate_percent_change(
            total_holdings, obj.price_change_7days
        )
        obj.percentage_change_30days = calculate_percent_change(
            total_holdings, obj.price_change_30days
        )
        obj.pecentage_change_1year = calculate_percent_change(
            total_holdings, obj.price_change_1year
        )
        obj.save()
    end_time = time.time()
    logging.info(
        f"Time taken to update percentage change for wallets : {end_time - start_time} seconds."
    )
    return f"Time taken to update percentage change for wallets : {end_time - start_time} seconds."


@shared_task(time_limit=1000)
def Recifi_alerts():
    """
    Fetches token addresses from Recifi wallets, calculates percentage changes
    for each token's occurrence among all wallets, and sends alerts if the
    percentage change exceeds 5%.
    """

    start = time.time()
    RecifiToken.admin_objects.all().delete()
    objs = Recifi.objects.all()
    for obj in objs:
        token_addresses = get_bought_token(obj.wallet_address)
        tokens = [
            RecifiToken(Recifi=obj, token_address=token_address)
            for token_address in token_addresses
        ]
        RecifiToken.objects.bulk_create(tokens)

    Recifi_tokens = RecifiToken.objects.values_list("token_address", flat=True)
    Recifi_tokens = set(Recifi_tokens)
    for token in Recifi_tokens:
        token_count = RecifiToken.objects.filter(token_address=token).count()
        if token_count > 0:
            total_tokens = objs.count()
            percentage_change = round((token_count / total_tokens) * 100, 2)
            if percentage_change > 5:
                notification_data = {
                    "percentage": percentage_change,
                    "symbol": get_token_symbol(to_checksum_address(token)),
                    "token_address": token,
                }
                send_Recifi_alert_notification(notification_data=notification_data)
    end = time.time()
    logging.info(
        f"Time taken to fetch token addresses from Recifi wallets : {end - start} seconds."
    )
    return f"Time taken to fetch token addresses from Recifi wallets : {end - start} seconds."


@shared_task()
def update_historical_price():
    """
    Updates the price change for each wallet in the Recifi model.
    """
    start = time.time()
    wallets = Recifi.objects.all()
    for wallet in wallets:
        wallet.price_change_7days = get_wallet_price_change(wallet.wallet_address, 7)
        wallet.price_change_30days = get_wallet_price_change(wallet.wallet_address, 30)
        wallet.price_change_1year = get_wallet_price_change(wallet.wallet_address, 365)
        wallet.save()
    end = time.time()
    logging.info(
        f"Time taken to update price change for wallets : {end - start} seconds."
    )
    return f"Time taken to update price change for wallets : {end - start} seconds."
