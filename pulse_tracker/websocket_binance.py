import json
import requests
import threading
import websocket
from django.conf import settings

from utils.helper import get_watchlist_symbols


def on_open(ws):
    """
    Handles WebSocket opening event.
    """
    print("opened connection")


def on_close(ws, close_status_code, close_msg):
    """
    Handles WebSocket closing event.
    """
    print("closed connection")
    ws.close()


def on_error(ws, error):
    """
    Handles WebSocket error event.
    """
    print(error)
    ws.close()


def on_message(ws, message, symbol):
    """
    Handles incoming WebSocket messages.
    """
    json_message = json.loads(message)
    percentage = float(
        json_message["P"]
    )  # 'P' is the percentage change in crypto price
    if percentage >= 100 or percentage <= -100:
        send_percentage_to_api(symbol, percentage)
    print("connection closed")
    ws.close()


def send_percentage_to_api(symbol, percentage):
    """
    Sends the percentage change to the API.
    """
    url = f"{settings.BACKEND_URL}/api/notify/"
    data = {"symbol": symbol, "percentage": percentage}
    requests.post(url, data)


def start_binance_websocket(symbol):
    """
    Starts a WebSocket connection to Binance for a given symbol.
    """
    socket = f"wss://stream.binance.com:9443/ws/{symbol}usdt@ticker"
    ws = websocket.WebSocketApp(
        socket,
        on_open=on_open,
        on_close=on_close,
        on_message=lambda ws, message: on_message(ws, message, symbol),
        on_error=on_error,
    )
    ws.run_forever()


def run_in_thread(symbol):
    """
    Runs the WebSocket connection in a separate thread.
    """
    thread = threading.Thread(target=start_binance_websocket, args=(symbol,))
    thread.daemon = True  # Daemonize thread to close when the main program exits
    thread.start()


def initialize_websockets():
    """
    Initializes WebSocket connections for all symbols in the watchlist.
    """
    symbols = get_watchlist_symbols()
    for pair in symbols:
        run_in_thread(pair.lower())
