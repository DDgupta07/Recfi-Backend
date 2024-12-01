import logging
import requests
from decimal import Decimal
from django.conf import settings
from datetime import datetime, timedelta, timezone

from .exceptions import CovalentAPIError
from .helper import calculate_percent_change, sum_all_quote


# Configure logging
logger = logging.getLogger(__name__)
logger_info = logging.getLogger("info")
logger_error = logging.getLogger("error")


def fetch_covalent_data(wallet_address):
    url = f"https://api.covalenthq.com/v1/1/address/{wallet_address}/balances_v2/?key={settings.COVALENT_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        logger_error.error(
            f"Error fetching data from Covalent API: {response.json()} {response.status_code}"
        )
        raise CovalentAPIError(
            f"Error fetching data from Covalent API: {response.status_code}"
        )

    data = response.json()

    if not data.get("data") or not data["data"].get("items"):
        logger_error.error(
            f"Invalid response structure from Covalent API : {data} - {response.status_code}"
        )
        raise CovalentAPIError("Invalid response structure from Covalent API.")

    return data["data"]["items"]


def get_wallet_holdings(wallet_address):
    items = fetch_covalent_data(wallet_address)[:5]
    tokens = []

    for item in items:
        balance_str = item.get("balance")
        contract_decimals = item.get("contract_decimals")
        if balance_str and contract_decimals:
            balance = Decimal(balance_str) / (10**contract_decimals)
        pretty_quote = item.get("pretty_quote")
        if balance and balance > 0 and pretty_quote is not None:
            contract_address = item.get("contract_address")
            token_info = {
                "symbol": item.get("contract_ticker_symbol"),
                "contract_name": item.get("contract_name"),
                "contract_address": contract_address,
                "balance": balance,
                "quote": item.get("quote"),
                "pretty_quote": item.get("pretty_quote"),
                "token_url": f"{settings.ETHERSCAN_URL}{contract_address}",
                "dex_url": f"{settings.DEXTOOLS_URL}{contract_address}",
            }
            tokens.append(token_info)
    return tokens


def get_wallet_24h_percentage_change(wallet_address):
    items = fetch_covalent_data(wallet_address)
    total_holdings = 0
    total_holdings_24h = 0

    for item in items:
        quote = item.get("quote", None)
        quote_24h = item.get("quote_24h", None)
        if quote and quote_24h:
            total_holdings += quote
            total_holdings_24h += quote_24h

    percent_change_24h = calculate_percent_change(total_holdings, total_holdings_24h)
    return percent_change_24h, Decimal(total_holdings)


def fetch_historical_data(wallet_address, date):
    url = (
        f"https://api.covalenthq.com/v1/1/address/{wallet_address}/historical_balances/"
    )
    response = requests.get(
        url, params={"key": settings.COVALENT_API_KEY, "date": date}
    )

    if response.status_code != 200:
        logger_error.error(
            f"Error fetching data from Covalent API: {response.json()} - {response.status_code}"
        )
        raise CovalentAPIError(
            f"Error fetching data from Covalent API: {response.status_code}"
        )

    data = response.json()

    if not data.get("data") or not data["data"].get("items"):
        logger_error.error(
            f"Invalid response structure from Covalent API : {data} - {response.status_code}"
        )
        raise CovalentAPIError("Invalid response structure from Covalent API")

    return data["data"]["items"]


def get_wallet_percentage_change(wallet_address, days_back):
    current_quote = sum_all_quote(fetch_covalent_data(wallet_address))
    back_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    historical_quote = sum_all_quote(fetch_historical_data(wallet_address, back_date))
    percent_change = calculate_percent_change(current_quote, historical_quote)
    return percent_change


def get_wallet_1week_percentage_change(wallet_address):
    return get_wallet_percentage_change(wallet_address, 7)


def get_wallet_1month_percentage_change(wallet_address):
    return get_wallet_percentage_change(wallet_address, 30)


def get_wallet_1year_percentage_change(wallet_address):
    return get_wallet_percentage_change(wallet_address, 365)


def get_wallet_price_change(wallet_address, days_back):
    # calculate the date days_back from today
    back_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    historical_quote = sum_all_quote(fetch_historical_data(wallet_address, back_date))
    return historical_quote


def fetch_recent_transactions(wallet_address, minutes=60):
    """
    Fetch recent transactions for the specified wallet address from the Covalent API.
    """
    url = f"https://api.covalenthq.com/v1/1/address/{wallet_address}/transactions_v3/"
    response = requests.get(url, params={"key": settings.COVALENT_API_KEY})

    if response.status_code != 200:
        logger_error.error(
            f"Error fetching data from Covalent API: {response.json()} - {response.status_code}"
        )
        raise CovalentAPIError(
            f"Error fetching data from Covalent API: {response.status_code}"
        )

    data = response.json()

    if not data.get("data") or "items" not in data["data"]:
        logger_error.error(
            f"Invalid response structure from Covalent API: {data} - {response.status_code}"
        )
        raise CovalentAPIError("Invalid response structure from Covalent API")

    transactions = data["data"]["items"]

    if not transactions:
        logger_error.info("No recent transactions found.")
        return []

    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(minutes=minutes)
    filtered_transactions = [
        tx
        for tx in transactions
        if datetime.strptime(tx["block_signed_at"], "%Y-%m-%dT%H:%M:%S%z")
        >= cutoff_time
    ]

    return filtered_transactions


def get_bought_token(wallet_address):
    """
    Get the addresses of tokens bought by the specified wallet address from recent transactions.
    """
    transactions = fetch_recent_transactions(wallet_address)
    bought_token_addresses = set()

    for transaction in transactions:
        for log_event in transaction.get("log_events", []):
            if is_token_bought_event(log_event, wallet_address):
                bought_token_addresses.add(log_event["sender_address"])

    return list(bought_token_addresses)


def is_token_bought_event(log_event, wallet_address):
    """
    Check if a log event indicates that a token was bought by the given wallet address.
    """
    if not log_event["decoded"]:
        return False

    event_name = log_event["decoded"]["name"]
    if event_name in ["Transfer", "Buy"]:
        for param in log_event["decoded"]["params"]:
            if (
                param["name"] == "to"
                and param["value"].lower() == wallet_address.lower()
            ):
                return True

    return False
