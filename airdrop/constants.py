from enum import Enum

COMMON_CNTRCT_PATH = '../resources/node_modules/singularitynet-airdrop-contracts'
AIRDROP_ADDR_PATH = COMMON_CNTRCT_PATH + '/networks/SingularityAirdrop.json'


class AirdropClaimStatus(Enum):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
