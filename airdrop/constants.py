import os
from enum import Enum
from airdrop.config import NETWORK_ID

COMMON_CNTRCT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'resources'))
AIRDROP_ADDR_PATH = COMMON_CNTRCT_PATH + \
                    '/singularitynet-airdrop-contracts/networks/SingularityAirdrop.json'
STAKING_CONTRACT_PATH = COMMON_CNTRCT_PATH + '/singularitynet-staking-contract'


class AirdropClaimStatus(Enum):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    NOT_STARTED = 'NOT_STARTED'


class AirdropEvents(Enum):
    AIRDROP_CLAIM = 'Claim'
    AIRDROP_WINDOW_OPEN = 'AirdropWindowOpen'


USER_REGISTRATION_SIGNATURE_FORMAT = {
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
        "name": "Nunet Airdrop",
        "version": "1",
        "chainId": NETWORK_ID,
    },
    "message": {
        "Airdrop": {
            "airdropId": 0,
            "airdropWindowId": 0,
            "blockNumber": 0,
            "walletAddress": "",
            "cardanoAddress": "",
        },

    },
}
