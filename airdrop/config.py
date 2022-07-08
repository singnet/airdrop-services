from enum import Enum

NETWORK = {
    "name": "test",
    "http_provider": "https://ropsten.infura.io",
    "ws_provider": "wss://ropsten.infura.io/ws",
    "db": {
        "DB_DRIVER": "mysql+pymysql",
        "DB_HOST": "localhost",
        "DB_USER": "unittest_root",
        "DB_PASSWORD": "unittest_pwd",
        "DB_NAME": "airdrop_unittest_db",
        "DB_PORT": 3306,
        "DB_LOGGING": True,
    },
}

BALANCE_DB_CONFIG = {
    "DB_DRIVER": "mysql+pymysql",
    "DB_HOST": "localhost",
    "DB_USER": "unittest_root",
    "DB_PASSWORD": "unittest_pwd",
    "DB_NAME": "token_balances",
    "DB_PORT": 3306,
    "DB_LOGGING": True,
}

NETWORK_ID = 3
SLACK_HOOK = {
    "hostname": "https://hooks.slack.com",
    "port": 443,
    "path": "",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "channel_name": "airdrop-ropsten-alerts"
}

SIGNER_PRIVATE_KEY = 'AIRDROP_SIGNER_PRIVATE_KEY'
SIGNER_PRIVATE_KEY_STORAGE_REGION = ''

AIRDROP_RECEIPT_SECRET_KEY = 'AIRDROP_RECEIPT_PRIVATE_KEY'
AIRDROP_RECEIPT_SECRET_KEY_STORAGE_REGION = ''

NUNET_SIGNER_PRIVATE_KEY = 'NUNET_AIRDROP_SIGNER_PRIVATE_KEY'
NUNET_SIGNER_PRIVATE_KEY_STORAGE_REGION = 'TestValue'

MAX_STAKE_LIMIT = 25000


class AirdropStrategy:
    AGIX = "AGIX"


class LoyaltyAirdropConfig(Enum):
    deposit_address = "addr"
    pre_claim_transfer_amount = {"amount": 2, "unit": "ADA"}
    network = "-testnet-magic 1097911063"
    chain = "Cardano"
