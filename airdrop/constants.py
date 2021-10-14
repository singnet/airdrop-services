import os
from enum import Enum

COMMON_CNTRCT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'resources', 'node_modules', 'singularitynet-airdrop-contracts'))
AIRDROP_ADDR_PATH = COMMON_CNTRCT_PATH + '/networks/SingularityAirdrop.json'


class AirdropClaimStatus(Enum):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    NOT_STARTED = 'NOT_STARTED'
