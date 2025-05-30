import os
from copy import deepcopy
from enum import Enum

from airdrop.config import NETWORK_ID, BlockFrostAPIBaseURL

PROCESSOR_PATH = "airdrop.processor"
COMMON_CNTRCT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))
AIRDROP_ADDR_PATH = COMMON_CNTRCT_PATH + "/singularitynet-airdrop-contracts/networks/SingularityAirdrop.json"
STAKING_CONTRACT_PATH = COMMON_CNTRCT_PATH + "/singularitynet-staking-contract"

ELIGIBILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "address": {"type": "string"}
    },
    "required": ["address", "airdrop_id", "airdrop_window_id"],
}

ADDRESS_ELIGIBILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "address": {"type": "string"},
    },
    "required": ["address", "airdrop_id"],
}

USER_REGISTRATION_SCHEMA = {
    "type": "object",
    "properties": {
        "address": {"type": "string"},
    },
    "required": ["address", "airdrop_id", "airdrop_window_id"],
}

CLAIM_SCHEMA = {
    "type": "object",
    "properties": {
        "address": {"type": "string"},
        "airdrop_id": {"type": "string"},
        "airdrop_window_id": {"type": "string"}
    },
    "required": ["address", "airdrop_id", "airdrop_window_id"],
}

DEPOSIT_EVENT_TX_METADATA = {
    "type": "object",
    "properties": {
        "r1": {"type": "string"},
        "r2": {"type": "string"},
        "wid": {"type": "string"}
    },
    "required": ["r1", "r2", "wid"]
}

USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
        ],
        "AirdropSignatureTypes": [
            {"name": "airdropId", "type": "uint256"},
            {"name": "airdropWindowId", "type": "uint256"},
            {"name": "blockNumber", "type": "uint256"},
            {"name": "walletAddress", "type": "address"},
        ],
        "Mail": [
            {"name": "Airdrop", "type": "AirdropSignatureTypes"},
        ],
    },
    "primaryType": "Mail",
    "domain": {
        "name": "",
        "version": "1",
        "chainId": NETWORK_ID,
    },
    "message": {
        "Airdrop": {
            "airdropId": 0,
            "airdropWindowId": 0,
            "blockNumber": 0,
            "walletAddress": ""
        },

    },
}
USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT = deepcopy(USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT)
USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT["types"]["AirdropSignatureTypes"] \
    .append({"name": "cardanoAddress", "type": "string"})
USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT["types"]["AirdropSignatureTypes"] \
    .append({"name": "cardanoWalletName", "type": "string"})
USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT["message"]["Airdrop"]["cardanoAddress"] = ""
USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT["message"]["Airdrop"]["cardanoWalletName"] = ""

USER_CLAIM_SIGNATURE_DEFAULT_FORMAT = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
        ],
        "AirdropSignatureTypes": [
            {"name": "airdropWindowId", "type": "uint256"},
            {"name": "receipt", "type": "string"},
        ],
        "Mail": [
            {"name": "Airdrop", "type": "AirdropSignatureTypes"},
        ],
    },
    "primaryType": "Mail",
    "domain": {
        "name": "",
        "version": "1",
        "chainId": NETWORK_ID,
    },
    "message": {
        "Airdrop": {
            "airdropWindowId": 0,
            "receipt": ""
        },

    },
}


class UserClaimStatus(Enum):
    RECEIVED = "RECEIVED"
    READY_TO_CLAIM = "READY_TO_CLAIM"
    NOT_REGISTERED = "NOT_REGISTERED"
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"


class AirdropClaimStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NOT_STARTED = "NOT_STARTED"
    ADA_RECEIVED = "ADA_RECEIVED"
    CLAIM_INITIATED = "CLAIM_INITIATED"
    CLAIM_FAILED = "CLAIM_FAILED"
    CLAIM_SUBMITTED = "CLAIM_SUBMITTED"


class AirdropEvents(Enum):
    AIRDROP_CLAIM = "Claim"
    AIRDROP_WINDOW_OPEN = "AirdropWindowOpen"


class BlockFrostAPI:
    get_last_block = BlockFrostAPIBaseURL + "/v0/blocks/latest"
    get_transaction_details = BlockFrostAPIBaseURL + "/v0/txs/{hash}"
    get_stake_address = BlockFrostAPIBaseURL + "/v0/addresses/{address}"
    get_account_associated_addresses = BlockFrostAPIBaseURL + "/v0/accounts/{stake_address}/addresses"


class TransactionType(Enum):
    CLAIM = "Claim"
    REGISTRATION = "Registration"


class CardanoEra(Enum):
    BYRON = "Byron"
    SHELLEY = "Shelley"
    ANY = "*"


CARDANO_ADDRESS_PREFIXES = {
    CardanoEra.BYRON: ["DdzFF", "Ae2", "37bt"],
    CardanoEra.SHELLEY: ["addr1", "addr_test1"]
}
CARDANO_ADDRESS_PREFIXES[CardanoEra.ANY] = [prefix for era in CARDANO_ADDRESS_PREFIXES.values() for prefix in era]
