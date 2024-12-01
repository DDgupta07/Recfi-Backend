from django.urls import path

from .views import (
    CryptoTradeView,
    ExecuteTrade,
    RecifiView,
    RecifiWalletHoldings,
    TradeDetailView,
    WalletPercentageChange,
)

urlpatterns = [
    path("trade/", CryptoTradeView.as_view(), name="crypto_trade"),
    path("execute-trade/", ExecuteTrade.as_view(), name="execute_trade"),
    path("Recifi-whale/", RecifiView.as_view(), name="Recifi_whale"),
    path("wallet-holdings/", RecifiWalletHoldings.as_view(), name="wallet_holdings"),
    path("trade/<uuid:uuid>/", TradeDetailView.as_view(), name="cancel_trade"),
    path(
        "pct-change/<str:wallet_address>/",
        WalletPercentageChange.as_view(),
        name="pct_change",
    ),
]
