from unittest import TestCase
from unittest.mock import Mock
from airdrop.application.services.airdrop_services import AirdropServices
from http import HTTPStatus
from airdrop.constants import AirdropClaimStatus
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.models import AirdropWindow, Airdrop
from datetime import datetime, timedelta


class AirdropClaims(TestCase):
    def setUp(self):

        org_name = 'SINGNET'
        token_name = 'AGIX'
        token_type = 'CONTRACT'
        portal_link = 'https://ropsten-airdrop.singularitynet.io/'
        documentation_link = 'https://ropsten-airdrop.singularitynet.io/'
        description = 'This is a test airdrop'
        github_link = 'https://github.com/singnet/airdrop-services'
        airdrop_window_name = 'Test Airdrop Window'
        airdrop_window_description = 'This is a test airdrop window'
        registration_required = True
        registration_start_date = datetime.utcnow()
        registration_end_date = datetime.utcnow() + timedelta(days=30)
        snapshot_required = True
        snapshot_start_date = datetime.utcnow()
        claim_start_date = datetime.utcnow()
        claim_end_date = datetime.utcnow() + timedelta(days=30)

        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        user_address = '0x176133a958449C28930970989dB5fFFbEdd9F449'

        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link)
        airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id, airdrop_window_name, airdrop_window_description, registration_required, registration_start_date, registration_end_date, snapshot_required, snapshot_start_date, claim_start_date, claim_end_date)

    def test_get_signature_for_airdrop_window_claim(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F449",
            "airdrop_id": "1",
            "airdrop_window_id": "1"
        }

        status_code, result = AirdropServices().airdrop_window_claims(payload)

        expected_reult = {
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
        }

        self.assertEqual(status_code, HTTPStatus.OK.value)
        assert result == expected_reult

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
        now = str(datetime.utcnow())

        expected_reult = {
            "status": 200,
            "data": {
                "claim_history": [
                    {
                        "airdrop_id": 1,
                        "airdrop_window_id": 1,
                        "user_address": "0x176133a958449C28930970989dB5fFFbEdd9F447",
                        "txn_hash": "0x54990b02618bb025e91f66bd253baa77522aff4b0140440f5aecdd463c24b2fc",
                        "txn_status": "SUCCESS",
                        "claimable_amount": 100,
                        "registered_at": now,
                        "is_eligible": True
                    }
                ]
            },
            "message": "OK"
        }

        self.assertEqual(status_code, HTTPStatus.OK.value)
        assert result == expected_reult

    def test_airdrop_window_claim_history(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "airdrop_id": "1",
            "airdrop_window_id": "1"
        }

        status_code, result = AirdropServices().airdrop_window_claim_history(payload)

        result_length = result['data']['claims'].__len__()

        self.assertLessEqual(result_length, 1)

    def tearDown(self):

        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        airdrop_repo = AirdropRepository()
        airdrop = airdrop_repo.get_token_address(token_address)
        airdrop_repo.session.query(Airdrop).filter(
            Airdrop.contract_address == contract_address).delete()
        airdrop_repo.session.query(AirdropWindow).filter(
            AirdropWindow.airdrop_id == airdrop.id).delete()
