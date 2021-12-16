import os
from enum import Enum

COMMON_CNTRCT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'resources', 'node_modules'))
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
