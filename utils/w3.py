import json
import logging
import requests
from django.conf import settings
from eth_account import Account
from eth_utils import to_checksum_address
from pathlib import Path
from web3 import Web3

logger = logging.getLogger(__name__)
logger_info = logging.getLogger("info")
logger_error = logging.getLogger("error")

w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))


def load_erc20_contract(address):
    abi_path = Path(__file__).resolve().parent / "erc_20_abi.json"
    with open(abi_path) as abi_file:
        erc20_abi = json.load(abi_file)
    return w3.eth.contract(address=to_checksum_address(address), abi=erc20_abi)


def create_wallet():
    """
    Create a new Ethereum wallet.
    """
    account = Account.create()
    keys = {
        "wallet_address": account.address,
        "private_key": account.key.hex(),
    }
    return keys


def import_wallet(private_key):
    """
    Import an existing Ethereum wallet using the private key.
    """
    return Account.from_key(private_key).address


def check_balance(address):
    """
    Check the Ether balance of an Ethereum wallet address.
    """
    balance = w3.eth.get_balance(address)
    return w3.from_wei(balance, "ether")


def transfer_token(private_key, wallet_address, receiver_address, amount):
    """
    Transfer Ether from one wallet to another.

    Raises:
        ValueError: If there are insufficient funds to cover the transfer and gas fees.
    """
    balance = check_balance(wallet_address)
    gas_price = w3.eth.gas_price
    gas_limit = 21000

    if amount == balance:
        gas_cost = gas_price * gas_limit
        value = w3.to_wei(balance, "ether") - gas_cost
        if value < 0:
            raise ValueError("Insufficient funds to cover gas fees.")
    else:
        value = w3.to_wei(amount, "ether")
        if balance < amount:
            raise ValueError(
                f"Insufficient funds as available balance is {balance} ETH, but {amount} ETH was requested."
            )

    nonce = w3.eth.get_transaction_count(wallet_address)
    logger_info.info(f"transfer token nonce for {wallet_address} : {nonce}")
    transaction = {
        "nonce": nonce,
        "to": receiver_address,
        "value": value,
        "gasPrice": gas_price,
        "gas": gas_limit,
    }
    logger_info.info(f"Transfering {amount} eth to {receiver_address}")
    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    logger_info.info(f"Transfered {amount} eth to {receiver_address}")
    return tx_hash.hex()


def transfer_erc20_token(
    private_key, wallet_address, receiver_address, amount, token_address
):
    """
    Transfer ERC-20 tokens from one wallet to another.

    Args:
        private_key (str): The private key of the sender's wallet.
        wallet_address (str): The sender's wallet address.
        receiver_address (str): The receiver's wallet address.
        amount (Decimal): The amount of tokens to transfer.
        token_address (str): The contract address of the ERC-20 token.

    """
    contract = load_erc20_contract(token_address)
    nonce = w3.eth.get_transaction_count(wallet_address)
    gas_price = w3.eth.gas_price
    gas_limit = 60000

    # Convert amount to smallest unit (e.g., wei for ETH, token's smallest unit for ERC-20)
    decimals = contract.functions.decimals().call()
    value = int(amount * (10**decimals))

    transaction = contract.functions.transfer(
        w3.to_checksum_address(receiver_address), value
    ).build_transaction(
        {
            "chainId": w3.eth.chain_id,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "nonce": nonce,
        }
    )

    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    logger_info.info(f"Transferred {amount} tokens to {receiver_address}")
    return tx_hash.hex()


def transfer_tx_fee(private_key, wallet_address, receiver_address, tx_fee, nonce):
    """
    Transfer Ether from one wallet to another.

    Raises:
        ValueError: If there are insufficient funds to cover the transfer and gas fees.
    """
    balance = check_balance(wallet_address)
    gas_price = w3.eth.gas_price
    gas_limit = 21000

    if tx_fee == balance:
        gas_cost = gas_price * gas_limit
        value = w3.to_wei(balance, "ether") - gas_cost
        if value < 0:
            raise ValueError("Insufficient funds to cover gas fees.")
    else:
        value = w3.to_wei(tx_fee, "ether")
        if balance < tx_fee:
            raise ValueError(
                f"Insufficient funds as available balance is {balance} ETH, but {tx_fee} ETH was requested."
            )

    logger_info.info(f"transfer token nonce for {wallet_address} : {nonce}")
    transaction = {
        "nonce": nonce,
        "to": receiver_address,
        "value": value,
        "gasPrice": gas_price,
        "gas": gas_limit,
    }
    logger_info.info(f"Transfering {tx_fee} eth to {receiver_address}")
    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    logger_info.info(f"Transfered {tx_fee} eth to {receiver_address}")
    return tx_hash.hex()


def check_balance_eth_usdt(address):
    """
    Check the Ether and USDT balance of an Ethereum wallet address.
    """
    usdt_contract_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    abi_path = Path(__file__).resolve().parent / "usdt_abi.json"
    with open(abi_path) as abi_file:
        usdt_abi = json.load(abi_file)
    usdt_contract = w3.eth.contract(address=usdt_contract_address, abi=usdt_abi)
    balance = w3.eth.get_balance(address)
    usdt_balance = usdt_contract.functions.balanceOf(address).call()
    return w3.from_wei(balance, "ether"), usdt_balance / (10**6)


def sell_eth_for_usdt(amount_eth, target_price, private_key, current_price):
    """
    Function to sell ETH for USDT if the current price of ETH is greater than the target price of ETH.
    """
    try:
        logger_info.info(
            f"Sell eth for usdt : amount_eth {amount_eth} and target_price {target_price}"
        )
        if current_price >= target_price:
            usdt_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
            tx = swap_eth_to_token(private_key, amount_eth, usdt_address)
            return True, tx
        else:
            message = f"Current price {current_price} is less than target price {target_price}"
            return False, message
    except Exception as e:
        logger_error.error(f"On calling sell_eth_for_usdt : {str(e)}")
        return False, str(e)


def buy_eth_from_usdt(amount_eth, target_price, private_key, current_price):
    """
    Function to buy ETH from USDT if the current price of ETH is less than the target price of ETH.
    """
    try:
        logger_info.info(
            f"Buy eth from usdt : amount_eth {amount_eth} and target_price {target_price}"
        )
        if current_price <= target_price:
            usdt_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
            tx = swap_token_to_eth(private_key, amount_eth, usdt_address)
            return True, tx
        else:
            message = f"Current price {current_price} is higher than target price {target_price}"
            return False, message
    except Exception as e:
        logger_error.error(f"On calling buy_eth_from_usdt : {str(e)}")
        return False, str(e)


def get_token_symbol(contract_address):
    """
    Get the symbol of an ERC-20 token contract.

    param contract_address: The Ethereum address of the token contract.
    return: The symbol of the token.
    """
    # ABI for the symbol function of an ERC-20 token
    erc20_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    ]

    contract = w3.eth.contract(address=contract_address, abi=erc20_abi)
    symbol = contract.functions.symbol().call()
    return symbol


def is_contract_address(address):
    """
    Check if an address is a contract address on Ethereum.

    :param address: The Ethereum address to check.
    :return: True if the address is a contract, False otherwise.
    """
    chain_id = w3.eth.chain_id
    if chain_id != 1:
        return True
    if w3.is_address(address):
        checksummed_address = to_checksum_address(address)
        code = w3.eth.get_code(checksummed_address)
        return code != b"0x" and code != b""
    else:
        return False


def swap_eth_to_token(
    private_key: str, amount_eth: float, token_address: str, is_transfer: bool = False
):
    """
    Example usage for buy tokens using ETH
    private_key = "0xYourPrivateKey"
    amount_eth = 0.1
    token_address = "0xYourTokenContractAddress"
    router_address = "0xUniswapV2Router02"
    """
    try:
        logger_info.info(
            f"Swap eth to token : amount_eth {amount_eth} and token_address {token_address}"
        )
        # Get the account address
        account = w3.eth.account.from_key(private_key).address
        balance = check_balance(account)
        tx_fee = (amount_eth * 1) / 100
        if (amount_eth + tx_fee) > balance:
            raise ValueError(
                "Insufficient ETH balance to cover the transaction amount."
            )

        deadline = w3.eth.get_block("latest")["timestamp"] + 3600  # 1 hour from now
        router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

        # Define the router contract ABI (simplified for demonstration)
        abi_path = Path(__file__).resolve().parent / "uniswap_abi_v2.json"
        with open(abi_path) as abi_file:
            router_abi = json.load(abi_file)

        # Set up the contract instance
        router_contract = w3.eth.contract(address=router_address, abi=router_abi)

        # Convert ETH amount to Wei
        amount_eth_wei = w3.to_wei(amount_eth, "ether")

        # Estimate the minimum amount of tokens to receive (considering slippage)
        min_tokens = 0

        # Build the transaction
        nonce = w3.eth.get_transaction_count(account, "pending")
        logger_info.info(f"swap_eth_to_token nonce for {account} : {nonce}")
        tx = router_contract.functions.swapExactETHForTokens(
            min_tokens,
            [
                w3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
                w3.to_checksum_address(token_address),
            ],
            account,
            deadline,
        ).build_transaction(
            {
                "from": account,
                "value": amount_eth_wei,
                "gas": 250000,
                "gasPrice": w3.eth.gas_price,
                "nonce": nonce,
            }
        )

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        if is_transfer:
            logger_info.info(f"Transfering fee {tx_fee} to Recifi whale wallet")
            transfer_tx_fee(
                private_key, account, settings.Recifi_WHALE_WALLET, tx_fee, nonce + 1
            )
            logger_info.info(f"Transfered fee {tx_fee} to Recifi whale wallet")
        return tx_hash.hex()
    except ValueError as e:
        logger_error.error(f"On calling swap_eth_to_token : {str(e)}")
        if "insufficient funds for gas * price + value" in str(e):
            raise ValueError(
                "Insufficient funds. Please ensure you have enough ETH to cover the transaction amount and gas fees."
            )
        elif "replacement transaction underpriced" in str(e):
            raise ValueError(
                "Replacement transaction underpriced. Kindly try again after some time."
            )
        raise ValueError(str(e))


def swap_token_to_eth(
    private_key: str, amount_token: float, token_address: str, is_transfer: bool = False
):
    """
    Example usage for selling tokens for ETH
    private_key = "0xYourPrivateKey"
    amount_token = 50
    token_address = "0xYourTokenContractAddress"
    """
    try:
        logger_info.info(
            f"Swap token to eth : amount_token {amount_token} and token_address {token_address}"
        )

        # Get the account address
        account = w3.eth.account.from_key(private_key).address

        if (
            token_address == "0xdAC17F958D2ee523a2206206994597C13D831ec7"
            and amount_token < 1
        ):
            raise ValueError("Minimum 1 USDT is required to proceed.")

        name, balance = get_token_balance(token_address, account)
        if amount_token > balance:
            raise ValueError(
                f"Insufficient {name} balance to cover the transaction amount."
            )

        deadline = w3.eth.get_block("latest")["timestamp"] + 3600  # 1 hour from now
        router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

        # Define the router contract ABI (simplified for demonstration)
        abi_path = Path(__file__).resolve().parent / "uniswap_abi_v2.json"
        with open(abi_path) as abi_file:
            router_abi = json.load(abi_file)

        # Simplified ERC20 ABI
        erc_abi_path = Path(__file__).resolve().parent / "erc_20_abi.json"
        with open(erc_abi_path) as abi_file:
            token_abi = json.load(abi_file)

        # Set up the contract instances
        router_contract = w3.eth.contract(address=router_address, abi=router_abi)
        token_contract = w3.eth.contract(address=token_address, abi=token_abi)

        # Convert token amount to smallest unit (e.g., Wei)
        amount_token_unit = token_contract.functions.decimals().call()
        amount_token_wei = int(amount_token * (10**amount_token_unit))

        eth_output = router_contract.functions.getAmountsOut(
            amount_token_wei,
            [
                w3.to_checksum_address(token_address),
                w3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
            ],
        ).call()[-1]

        eth_output_ether = w3.from_wei(eth_output, "ether")

        min_eth = 0

        nonce = w3.eth.get_transaction_count(account, "pending")
        logger_info.info(f"swap_token_to_eth approve nonce for {account} : {nonce}")
        approve_tx = token_contract.functions.approve(
            router_address, amount_token_wei
        ).build_transaction(
            {
                "from": account,
                "gas": 100000,
                "gasPrice": w3.eth.gas_price,
                "nonce": nonce,
            }
        )
        signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
        w3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)

        # Build the transaction
        nonce += 1
        logger_info.info(f"swap_token_to_eth nonce for {account} : {nonce}")
        tx = router_contract.functions.swapExactTokensForETH(
            amount_token_wei,
            min_eth,
            [
                w3.to_checksum_address(token_address),
                w3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
            ],
            account,
            deadline,
        ).build_transaction(
            {
                "from": account,
                "gas": 250000,
                "gasPrice": w3.eth.gas_price,
                "nonce": nonce,
            }
        )

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        if is_transfer:
            transfer_tx_fee(
                private_key,
                account,
                settings.Recifi_WHALE_WALLET,
                ((eth_output_ether * 1) / 100),
                nonce + 1,
            )
        return tx_hash.hex()
    except ValueError as e:
        logger_error.error(f"On calling swap_token_to_eth : {str(e)}")
        if "insufficient funds for gas * price + value" in str(e):
            raise ValueError(
                "Insufficient funds. Please ensure you have enough ETH to cover the transaction amount and gas fees."
            )
        elif "replacement transaction underpriced" in str(e):
            raise ValueError(
                "Replacement transaction underpriced. Kindly try again after some time."
            )
        raise ValueError(str(e))


def get_existing_nonce(wallet_address):
    nonce = w3.eth.get_transaction_count(wallet_address, "pending")
    return nonce


def replace_pending_transaction(private_key: str, gas_price_in_gwei: int):
    account = w3.eth.account.from_key(private_key).address
    nonce = get_existing_nonce(account)

    tx = {
        "nonce": nonce,
        "to": account,
        "value": 0,
        "gas": 21000,
        "gasPrice": w3.to_wei(gas_price_in_gwei, "gwei"),
    }

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return tx_hash.hex()


def has_pending_transactions(wallet_address):
    pending_nonce = w3.eth.get_transaction_count(wallet_address, "pending")
    completed_nonce = w3.eth.get_transaction_count(wallet_address, "latest")
    if pending_nonce > completed_nonce:
        return True
    else:
        return False


def get_token_info(token_contract, address):
    try:
        decimals = token_contract.functions.decimals().call()
    except Exception as e:
        print(e)
        return None, None
    balance = token_contract.functions.balanceOf(address).call() / (10**decimals)
    name = token_contract.functions.name().call()
    return name, balance


def get_token_transactions(address):
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": settings.ETHERSCAN_API_KEY,
    }
    try:
        response = requests.get(settings.ETHERSCAN_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "1":
            return data["result"]
        else:
            return []
    except Exception as e:
        print(e)
        return []


def get_token_holding(wallet_address):
    eth_balance = check_balance(wallet_address)

    token_txns = get_token_transactions(wallet_address)
    token_addresses = set(txn["contractAddress"] for txn in token_txns)

    token_balances = []
    for token_address in token_addresses:
        token_contract = load_erc20_contract(token_address)
        token_name, balance = get_token_info(token_contract, wallet_address)
        if token_name is not None and balance is not None:
            token_balances.append(
                {
                    "name": token_name,
                    "balance": balance,
                }
            )
    return {
        "eth_balance": eth_balance,
        "token_holdings": token_balances,
    }


def get_token_balance(token_address, wallet_address):
    try:
        token_contract = load_erc20_contract(token_address)
        decimals = token_contract.functions.decimals().call()
    except Exception as e:
        print(e)
        return None, 0
    balance = token_contract.functions.balanceOf(wallet_address).call() / (10**decimals)
    name = token_contract.functions.name().call()
    return name, balance


def get_current_gwei():
    return w3.eth.gas_price / (10**9)
