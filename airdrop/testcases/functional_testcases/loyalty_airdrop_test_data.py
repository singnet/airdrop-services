from datetime import datetime as dt
from datetime import timedelta

from web3 import Web3

from airdrop.processor.loyalty_airdrop import LoyaltyAirdrop

SECRETS_MANAGER_MOCK_VALUE = "c4162244e5ec8f53a51ab6bb0a29c50432d82afd0a168e6e5c5c55c43b0a9c9"


class LoyaltyAirdropData:
    token_address = "0x5e94577b949a56279637ff74dfcff2c28408f049"
    org_name = "SingularityNet"
    token_name = "AGIX"
    token_type = "CONTRACT"
    contract_address = "n/a"
    portal_link = "http://localhost/"
    documentation_link = "http://testlink.test"
    description = "Test description."
    github_link = "https://github.com/test-repository"
    airdrop_processor = "loyalty_airdrop.LoyaltyAirdrop"


class LoyaltyAirdropWindow1Data:
    airdrop_window_name = "Loyalty Airdrop Window 1"
    description = "Loyalty Airdrop Window 1"
    registration_required = False
    registration_start_date = dt.utcnow() - timedelta(days=2)
    registration_end_date = dt.utcnow() + timedelta(days=30)
    snapshot_required = False
    claim_start_date = dt.utcnow() - timedelta(days=2)
    claim_end_date = dt.utcnow() + timedelta(days=30)
    total_airdrop_tokens = 1000000


class LoyaltyAirdropWindow2Data:
    airdrop_window_name = "Loyalty Airdrop Window 2"
    description = 'Loyalty Airdrop Window 2'
    registration_required = False
    registration_start_date = dt.utcnow() + timedelta(days=25)
    registration_end_date = dt.utcnow() + timedelta(days=30)
    snapshot_required = False
    claim_start_date = dt.utcnow() + timedelta(days=45)
    claim_end_date = dt.utcnow() + timedelta(days=60)
    total_airdrop_tokens = 2000000


class LoyaltyAirdropWindow3Data:
    airdrop_window_name = "Loyalty Airdrop Window 3"
    description = 'Loyalty Airdrop Window 3'
    registration_required = False
    registration_start_date = dt.utcnow() - timedelta(days=25)
    registration_end_date = dt.utcnow() - timedelta(days=30)
    snapshot_required = False
    claim_start_date = dt.utcnow() + timedelta(days=45)
    claim_end_date = dt.utcnow() + timedelta(days=60)
    total_airdrop_tokens = 2000000


class LoyaltyAirdropUser1:
    address = Web3.toChecksumAddress("0x4e1388Acfd6237aeED2b01Da0d4ccFe242e8F6cA")
    private_key = bytes.fromhex("1c4162244e5ec8f53a51ab6bb0a29c50432d82afd0a168e6e5c5c55c43b0a9c9")
    cardano_address = "addr_test1qqera830frgpvw9f0jj2873lwe8nd8vcsf0q0ftuqqgd9g8ucaczw427uq8y7axn2v3w8dua87kjgdgu" \
                      "rmgl38vd2hysk4dfj9"
    signature_details = {
        "domain_name": LoyaltyAirdrop(None, None).domain_name,
        "block_no": 12432452
    }
    receipt_generated = "VkMBsWZsK1bn3mxXQlhPxW8FWzKvewws+yZjHourUGpsIkV0ytus2JrIWs9uA8x5q0le4cMyqmJNmq+2ZbLanxw="
