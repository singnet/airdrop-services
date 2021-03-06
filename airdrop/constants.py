import os
from copy import deepcopy
from enum import Enum

from airdrop.config import NETWORK_ID

PROCESSOR_PATH = "airdrop.processor"
COMMON_CNTRCT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources'))
AIRDROP_ADDR_PATH = COMMON_CNTRCT_PATH + '/singularitynet-airdrop-contracts/networks/SingularityAirdrop.json'
STAKING_CONTRACT_PATH = COMMON_CNTRCT_PATH + '/singularitynet-staking-contract'

ELIGIBILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "address": {"type": "string"}
    },
    "required": ["address", "airdrop_id", "airdrop_window_id"],
}
USER_REGISTRATION_SCHEMA = {
    "type": "object",
    "properties": {
        "address": {"type": "string"},
        "signature": {"type": "string"},
    },
    "required": ["signature", "address", "airdrop_id", "airdrop_window_id", "block_number"],
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
USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT["message"]["Airdrop"]["cardanoAddress"] = ""


class AirdropClaimStatus(Enum):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    NOT_STARTED = 'NOT_STARTED'


class AirdropEvents(Enum):
    AIRDROP_CLAIM = 'Claim'
    AIRDROP_WINDOW_OPEN = 'AirdropWindowOpen'
