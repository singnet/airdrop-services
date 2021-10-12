from unittest import TestCase
from common.utils import generate_claim_signature, read_contract_address
from airdrop.config import NETWORK_ID
from airdrop.constants import AIRDROP_ADDR_PATH


class SignatureCreation(TestCase):
    def test_valid_signature_creation(self):

        expected_signature = "0x878129aee1f81eea5bab526cc4a61d1a3b6fd728c39644197b2e0049ec817227105f2a46ac3b1e6403cd655d38ad609cca9c78fd93efd184116bd08d535a99891b"

        private_key = '92b7972e86b2f45f130a3089ff1908d00d8fed70dc9b7b002c6676d983776001'
        airdrop_window_id = "1"
        airdrop_id = "1"
        amount = 100
        user_address = "0x176133a958449C28930970989dB5fFFbEdd9F448"
        token_address = "0x176133a958449c28930970989db5fffbedd9f447"
        contract_address = read_contract_address(
            net_id=NETWORK_ID, path=AIRDROP_ADDR_PATH, key='address')

        generated_signature = generate_claim_signature(
            amount, airdrop_id, airdrop_window_id, user_address, contract_address, token_address, private_key)

        self.assertEqual(generated_signature, expected_signature)

    def test_invalid_signature_creation(self):
        expected_signature = "0x878129aee1f81eea5bab526cc4a61d1a3b6fd728c39644197b2e0049ec817227105f2a46ac3b1e6403cd655d38ad609cca9c78fd93efd184116bd08d535a99891b"

        private_key = '12b7972e86b2f45f130a3089ff1908d00d8fed70dc9b7b002c6656d983776001'
        airdrop_window_id = "1"
        airdrop_id = "1"
        amount = 100
        user_address = "0x171133a958449C18130970989dB5fFFbEdd9F448"
        token_address = "0x176133a958449c28930970989db5fffbedd9f447"
        contract_address = read_contract_address(
            net_id=NETWORK_ID, path=AIRDROP_ADDR_PATH, key='address')

        generated_signature = generate_claim_signature(
            amount, airdrop_id, airdrop_window_id, user_address, contract_address, token_address, private_key)

        self.assertNotEqual(generated_signature, expected_signature)
