import unittest
from unittest import TestCase
from unittest.mock import patch

from airdrop.config import NETWORK_ID
from airdrop.constants import AIRDROP_ADDR_PATH
from common.utils import generate_claim_signature, read_contract_address


class SignatureCreation(TestCase):

    @patch('common.utils.read_contract_address')
    def test_valid_signature_creation(self, read_contract_address):

        expected_signature = "0xdf107f59f19561b5fae0af2c597b965f6face8a67869e1d18f37e37b1a2369250f1a9cbef7eb198ad66c5cc88b72c8416a06cf80655dce526c020a8ffe05405e1b"
        read_contract_address.return_value = '0x176133a958449C28930970989dB5fFFbEdd9F448'

        private_key = '0aecc010b70ec65590fbfcb5c8c2936d994ff713e67268f12ca6499691c5a1e0'
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

    @patch('common.utils.read_contract_address')
    def test_invalid_signature_creation(self, read_contract_address):
        expected_signature = "0xdf107f59f19561b5fae0af2c597b965f6face8a67869e1d18f37e37b1a2369250f1a9cbef7eb198ad66c5cc88b72c8416a06cf80655dce526c020a8ffe05405e1b"
        read_contract_address.return_value = '0x176133a958449C28930970989dB5fFFbEdd9F448'

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
