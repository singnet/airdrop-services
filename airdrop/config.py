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

TOKEN_SNAPSHOT_DB_CONFIG = {
    "DB_DRIVER": "mysql+pymysql",
    "DB_HOST": "localhost",
    "DB_USER": "unittest_root",
    "DB_PASSWORD": "unittest_pwd",
    "DB_NAME": "token_snapshot_unittest_db",
    "DB_PORT": 3306,
    "DB_LOGGING": True,
}

NETWORK_ID = 3
DEFAULT_REGION = "us-east-1"
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
MIN_BLOCK_CONFIRMATION_REQUIRED = 5


class AirdropStrategy:
    AGIX = "AGIX"


class LoyaltyAirdropConfig(Enum):
    deposit_address = "addr"
    claim_address = "addr"
    pre_claim_transfer_amount = {"amount": 2, "unit": "ADA"}
    chain = "Cardano"


class BlockFrostAccountDetails:
    project_id = ""


class DepositDetails:
    address = "addr_test1qqllt2lmzypu9y9j9p6hgrcu9narh8rqczkdujqvqmqq4f9w9zv7f7pu6wefmn4t06y9e9ljggpjul3awg0p8tz664f" \
              "se7qsex"
    amount_in_lovelace = "2000000"


class TokenTransferCardanoService:
    url = "http://127.0.0.1:5005/cardano/AGIX/transfer"
    http_method = "post"
    headers = {'content-type': 'application/json'}


BlockFrostAPIBaseURL = "https://cardano-testnet.blockfrost.io/api"

TOTAL_WALLET_BALANCE_IN_COGS = 0
TOTAL_STAKE_BALANCE_IN_COGS = 0
TOTAL_LOYALTY_REWARD_IN_COGS = 0
