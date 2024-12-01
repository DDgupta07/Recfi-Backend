from django.apps import AppConfig


class TradeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trade"

    def ready(self) -> None:
        from .binance_websocket import run_in_thread

        run_in_thread()
