from unittest import TestCase
from unittest.mock import Mock
from airdrop.application.services.airdrop_services import AirdropServices
from http import HTTPStatus
from airdrop.constants import AirdropClaimStatus


class AirdropClaims(TestCase):
    def test_get_signature_for_airdrop_window_claim(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F449",
            "airdrop_id": "1",
            "airdrop_window_id": "1"
        }

        status_code, result = AirdropServices().airdrop_window_claims(payload)

        expected_reult = Mock({
            "status": 200,
            "data": {
                "claim": {
                    "airdrop_id": "1",
                    "airdrop_window_id": "1",
                    "user_address": "0x176133a958449C28930970989dB5fFFbEdd9F449",
                    "signature": "0xcb2ce8ea4749f58f0ea3cee7b5ed7686c67ccd1179dd526e080d6aa7fde69f70",
                    "claimable_amount": "100",
                    "token_address": "0x5e94577b949a56279637ff74dfcff2c28408f049"
                }
            },
            "message": "OK"
        })

        self.assertEqual(status_code, HTTPStatus.OK.value)
        self.assertEqual(expected_reult, result)

    def test_get_signature_for_airdrop_window_claim_with_invalid_windows(self):
        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F442",
            "airdrop_id": "100",
            "airdrop_window_id": "100"
        }

        status_code, result = AirdropServices().airdrop_window_claims(payload)

        self.assertNotEqual(status_code, HTTPStatus.BAD_REQUEST.value)

    def test_airdrop_window_claim_txn_status(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "airdrop_id": "1",
            "airdrop_window_id": "1",
            "txn_status": AirdropClaimStatus.SUCCESS,
            "txn_hash": "0xcb2ce8ea4749f58f0ea3cee7b5ed7686c67ccd1179dd526e080d6aa7fde69f70",
            "amount": "100"
        }

        status_code, result = AirdropServices().airdrop_window_claim_status(payload)

        self.assertEqual(status_code, HTTPStatus.OK.value)

    def test_airdrop_window_claim_duplicate_txn_status(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "airdrop_id": "1",
            "airdrop_window_id": "1",
            "txn_status": AirdropClaimStatus.SUCCESS,
            "txn_hash": "0xcb2ce8ea4749f58f0ea3cee7b5ed7686c67ccd1179dd526e080d6aa7fde69f70",
            "amount": "100"
        }

        status_code, result = AirdropServices().airdrop_window_claim_status(payload)

        self.assertEqual(status_code, HTTPStatus.BAD_REQUEST.value)

    def test_airdrop_window_claim_history(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F447",
            "airdrop_id": "1"
        }

        status_code, result = AirdropServices().airdrop_window_claim_history(payload)

        expected_reult = Mock({
            "status": 200,
            "data": {
                "claim_history": [
                    {
                        "airdrop_id": 1,
                        "airdrop_window_id": 1,
                        "user_address": "0x176133a958449C28930970989dB5fFFbEdd9F447",
                        "txn_hash": "0x54990b02618bb025e91f66bd253baa77522aff4b0140440f5aecdd463c24b2fc",
                        "txn_status": "SUCCESS",
                        "claimable_amount": 100
                    }
                ]
            },
            "message": "OK"
        })

        self.assertEqual(status_code, HTTPStatus.OK.value)
        self.assertEqual(expected_reult, result)

    def test_airdrop_window_claim_history(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "airdrop_id": "1",
            "airdrop_window_id": "1"
        }

        status_code, result = AirdropServices().airdrop_window_claim_history(payload)

        result_length = result['data']['claims'].__len__()

        self.assertLessEqual(result_length, 1)
