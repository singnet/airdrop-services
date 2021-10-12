from unittest import TestCase
from airdrop.application.services.airdrop_services import AirdropServices
from http import HTTPStatus


class AirdropClaims(TestCase):
    def test_get_signature_for_airdrop_window_claim(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F449",
            "airdrop_id": "1",
            "airdrop_window_id": "1"
        }

        status_code, result = AirdropServices().airdrop_window_claims(payload)

        self.assertEqual(status_code, HTTPStatus.OK.value)

    def test_get_signature_for_airdrop_window_claim_with_invalid_windows(self):
        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F442",
            "airdrop_id": "100",
            "airdrop_window_id": "100"
        }

        status_code, result = AirdropServices().airdrop_window_claims(payload)

        self.assertNotEqual(status_code, HTTPStatus.BAD_REQUEST.value)
