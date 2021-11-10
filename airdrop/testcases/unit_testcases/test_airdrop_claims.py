import unittest
from unittest import TestCase
from unittest.mock import Mock, patch
from airdrop.application.services.airdrop_services import AirdropServices
from http import HTTPStatus
from airdrop.constants import AirdropClaimStatus
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.models import AirdropWindow, Airdrop
from datetime import datetime, timedelta
from airdrop.application.services.user_registration_services import \
    UserRegistrationServices


class AirdropClaims(TestCase):
    def setUp(self):

        org_name = 'SINGNET'
        token_name = 'AGIX'
        token_type = 'CONTRACT'
        portal_link = 'https://ropsten-airdrop.singularitynet.io/'
        documentation_link = 'https://ropsten-airdrop.singularitynet.io/'
        description = 'This is a test airdrop'
        github_link = 'https://github.com/singnet/airdrop-services'
        registration_start_date = datetime.utcnow() - timedelta(days=2)
        registration_end_date = datetime.utcnow() + timedelta(days=30)
        claim_start_date = datetime.utcnow() - timedelta(days=2)
        claim_end_date = datetime.utcnow() + timedelta(days=30)

        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        user_address = '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'

        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link)
        airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id, airdrop_window_name='Airdrop Window 1', description='Long description', registration_required=True,
                                                   registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)

    @patch('common.utils.recover_address')
    @patch('airdrop.infrastructure.repositories.user_repository.UserRepository.check_rewards_awarded')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_signature_for_airdrop_window_id')
    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_amount')
    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.is_claimed_airdrop_window')
    def test_get_signature_for_airdrop_window_claim(self, mock_is_claimed_airdrop_window, mock_get_airdrop_window_claimable_amount, mock_get_signature_for_airdrop_window_id, mock_check_rewards_awarded, mock_recover_address):

        address = '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'
        airdrop_claim_signature = '958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F'

        mock_is_claimed_airdrop_window.return_value = {}
        mock_check_rewards_awarded.return_value = True, 1000
        mock_get_signature_for_airdrop_window_id.return_value = airdrop_claim_signature
        mock_get_airdrop_window_claimable_amount.return_value = 100, address

        mock_recover_address.return_value = address
        mock_check_rewards_awarded.value = True, 1000
        user_registration_payload = {
            "airdrop_window_id": "1",
            "airdrop_id": "1",
            "address": address,
            "signature": "958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F",
        }

        UserRegistrationServices().register(user_registration_payload)

        payload = {
            "address": address,
            "airdrop_id": "1",
            "airdrop_window_id": "1"
        }

        expected_response = {'airdrop_id': '1', 'airdrop_window_id': '1', 'user_address': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8',
                             'signature': '958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F', 'claimable_amount': 100, 'token_address': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'}

        status_code, result = AirdropServices().airdrop_window_claims(payload)
        self.assertEqual(expected_response, result)

    def test_get_signature_for_airdrop_window_claim_with_invalid_windows(self):
        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F442",
            "airdrop_id": "100",
            "airdrop_window_id": "100"
        }

        status_code, result = AirdropServices().airdrop_window_claims(payload)

        self.assertNotEqual(status_code, HTTPStatus.OK)

    def test_airdrop_window_claim_txn_status(self):

        payload = {
            "address": "0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8",
            "airdrop_id": "1",
            "airdrop_window_id": "1",
            "txn_status": "SUCCESS",
            "txn_hash": "0xcb2ce8ea4749f58f0ea3cee7b5ed7686c67ccd1179dd526e080d6aa7fde69f70",
            "amount": "100"
        }

        status_code, result = AirdropServices().airdrop_window_claim_status(payload)
        self.assertEqual(status_code, HTTPStatus.BAD_REQUEST)

    def test_airdrop_window_claim_duplicate_txn_status(self):

        payload = {
            "address": "0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8",
            "airdrop_id": "1",
            "airdrop_window_id": "1",
            "txn_status": "SUCCESS",
            "txn_hash": "0xcb2ce8ea4749f58f0ea3cee7b5ed7686c67ccd1179dd526e080d6aa7fde69f70",
            "amount": "100"
        }

        status_code, result = AirdropServices().airdrop_window_claim_status(payload)

        self.assertEqual(status_code, HTTPStatus.BAD_REQUEST.value)

    def test_airdrop_window_claim_history(self):

        payload = {
            "address": "0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8",
            "airdrop_id": "1"
        }

        status_code, result = AirdropServices().airdrop_window_claim_history(payload)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    def test_airdrop_window_claim_history(self):

        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "airdrop_id": "1",
            "airdrop_window_id": "1"
        }

        status_code, result = AirdropServices().airdrop_window_claim_history(payload)

        result_length = len(result['claim_history'])

        self.assertEqual(result_length, 0)

    def test_airdrop_listen_to_events(self):

        payload = {
            "transactionHash": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "json_str": {'authorizer': '0xD93209FDC420e8298bDFA3dBe340F366Faf1E7bc', 'claimer': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8', 'amount': 100, 'airDropId': 1, 'airDropWindowId': 1},
            "event": "Claim"
        }

        event = {"data": payload}

        response = AirdropServices().airdrop_listen_to_events(event)

        self.assertEqual(response, True)

    def test_airdrop_listen_to_events_with_duplicate_data(self):

        payload = {
            "transactionHash": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "json_str": {'authorizer': '0xD93209FDC420e8298bDFA3dBe340F366Faf1E7bc', 'claimer': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8', 'amount': 100, 'airDropId': 1, 'airDropWindowId': 1},
            "event": "Claim"
        }

        event = {"data": payload}

        response = AirdropServices().airdrop_listen_to_events(event)

        self.assertNotEqual(response, False)

    def test_airdrop_listen_to_events_with_invalid_event(self):

        payload = {
            "transactionHash": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "json_str": "{'conversionAuthorizer': '0xD93209FDC420e8298bDFA3dBe340F366Faf1E7bc'}",
            "event": "NewAuthorizer"
        }

        event = {"data": payload}

        response = AirdropServices().airdrop_listen_to_events(event)

        self.assertEqual(response, None)
