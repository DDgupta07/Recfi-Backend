from django.urls import path

from .views import (
    CreateWallet,
    ImportWallet,
    UserWalletView,
    WalletView,
    DefaultWalletView,
    TransferToken,
    SellBotVerification,
    TransactionHistory,
    TokenHoldingView,
    EthUsdtBalance,
    TokenBalanceView,
    CurrentGweiView,
    TransferErc20Token,
)


urlpatterns = [
    path("create-wallet/", CreateWallet.as_view(), name="create_wallet"),
    path("import-wallet/", ImportWallet.as_view(), name="import_wallet"),
    path("user-wallet/", UserWalletView.as_view(), name="wallets"),
    path("wallet/<uuid:uuid>/", WalletView.as_view(), name="wallet_view"),
    path("default-wallet/", DefaultWalletView.as_view(), name="default_wallet"),
    path("transfer-token/", TransferToken.as_view(), name="transfer_token"),
    path("verify-sell-bot/", SellBotVerification.as_view(), name="verify_sell_bot"),
    path("transaction-history/", TransactionHistory.as_view(), name="tx_history"),
    path("token-holdings/", TokenHoldingView.as_view(), name="token_holdings"),
    path("eth-usdt-balance/", EthUsdtBalance.as_view(), name="eth_usdt_balance"),
    path("token-balance/", TokenBalanceView.as_view(), name="token_balance"),
    path("gwei/", CurrentGweiView.as_view(), name="current_gwei"),
    path(
        "transfer-custom-token/",
        TransferErc20Token.as_view(),
        name="transfer_custom_token",
    ),
]
