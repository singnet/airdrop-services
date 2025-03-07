from datetime import timedelta

from web3 import Web3

from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.utils import datetime_in_utcnow

SECRETS_MANAGER_MOCK_VALUE = "c4162244e5ec8f53a51ab6bb0a29c50432d82afd0a168e6e5c5c55c43b0a9c9"


class NuNetAirdropData:
    token_address = "0x5e94577b949a56279637ff74dfcff2c28408f049"
    org_name = "NuNet"
    token_name = "AGIX"
    token_type = "CONTRACT"
    contract_address = "0x5e94577b949a56279637ff74dfcff2c28408f049"
    portal_link = "http://localhost/"
    documentation_link = "http://testlink.test"
    description = "Test description."
    github_link = "https://github.com/test-repository"
    airdrop_processor = "nunet_airdrop.NunetAirdrop"


class NuNetAirdropWindow1Data:
    airdrop_window_name = "NuNet Airdrop Window 1"
    description = "NuNet Airdrop Window 1"
    registration_required = True
    registration_start_date = datetime_in_utcnow() - timedelta(days=2)
    registration_end_date = datetime_in_utcnow() + timedelta(days=30)
    snapshot_required = True
    claim_start_date = datetime_in_utcnow() - timedelta(days=2)
    claim_end_date = datetime_in_utcnow() + timedelta(days=30)
    total_airdrop_tokens = 1000000


class NuNetAirdropWindow2Data:
    airdrop_window_name = "NuNet Airdrop Window 2"
    description = "NuNet Airdrop Window 2"
    registration_required = True
    registration_start_date = datetime_in_utcnow() + timedelta(days=25)
    registration_end_date = datetime_in_utcnow() + timedelta(days=30)
    snapshot_required = True
    claim_start_date = datetime_in_utcnow() + timedelta(days=45)
    claim_end_date = datetime_in_utcnow() + timedelta(days=30)
    total_airdrop_tokens = 1000000


class NuNetAirdropUser1:
    address = Web3.to_checksum_address("0x4e1388Acfd6237aeED2b01Da0d4ccFe242e8F6cA")
    private_key = bytes.fromhex("1c4162244e5ec8f53a51ab6bb0a29c50432d82afd0a168e6e5c5c55c43b0a9c9")
    signature_details = {
        "domain_name": DefaultAirdrop(None, None).domain_name,
        "block_no": 12432452
    }
    receipt_generated = ""
