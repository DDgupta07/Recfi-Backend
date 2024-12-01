import json
import requests
import threading
import websocket
from django.conf import settings


def on_open(ws):
    """
    Handles WebSocket opening event.
    """
    print("opened connection")


def on_close(ws):
    """
    Handles WebSocket closing event.
    """
    print("closed connection")


def on_error(ws, error):
    """
    Handles WebSocket error event.
    """
    print(error)


def on_message(ws, message):
    """
    Handles incoming WebSocket messages.
    """
    json_message = json.loads(message)
    candle = json_message["k"]
    close = candle["c"]
    send_close_price_to_api(close)


def send_close_price_to_api(close_price):
    """
    Sends the close price to the API.
    """
    url = f"{settings.BACKEND_URL}/api/execute-trade/"
    json_data = {"close_price": close_price}
    requests.post(url, json=json_data)


def start_binance_websocket():
    """
    Starts a WebSocket connection to Binance for ETH/USDT.
    """
    socket = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
    ws = websocket.WebSocketApp(
        socket,
        on_open=on_open,
        on_close=on_close,
        on_message=on_message,
        on_error=on_error,
    )
    ws.run_forever()


def run_in_thread():
    """
    Runs the Binance WebSocket in a separate thread.
    """

    thread = threading.Thread(target=start_binance_websocket)
    thread.daemon = True  # Daemonize thread to close when the main program exits
    thread.start()
