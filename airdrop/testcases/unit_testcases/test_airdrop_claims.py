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
from airdrop.utils import datetime_in_utcnow


class AirdropClaims(TestCase):
    airdrop_id = None
    airdrop_window_id = None
    def setUp(self):

        org_name = 'SINGNET'
        token_name = 'AGIX'
        token_type = 'CONTRACT'
        portal_link = 'https://ropsten-airdrop.singularitynet.io/'
        documentation_link = 'https://ropsten-airdrop.singularitynet.io/'
        description = 'This is a test airdrop'
        github_link = 'https://github.com/singnet/airdrop-services'
        registration_start_date = datetime_in_utcnow() - timedelta(days=2)
        registration_end_date = datetime_in_utcnow() + timedelta(days=30)
        claim_start_date = datetime_in_utcnow() - timedelta(days=2)
        claim_end_date = datetime_in_utcnow() + timedelta(days=30)

        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        user_address = '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'
        token_name = 'AGIX'

        occam_contract_address = '0x6e94577b949a56279637ff74dfcff2c28408f049'
        occam_token_address = '0x5e93577b949a56279637ff74dfcff2c28408f049'
        occam_user_address = '0xEA6741dDe714fd979de3EdF0F56AA9716B898ec8'
        occam_token_name = 'AGIX'

        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link)
        airdrop_windows =  airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id, airdrop_window_name='Airdrop Window 1', description='Long description', registration_required=True,
                                                   registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)
        global airdrop_id
        airdrop_id = airdrop.id
        global airdrop_window_id
        airdrop_window_id = airdrop_windows.id
        nunet_occam_airdrop = airdrop_repository.register_airdrop(
            occam_token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link)
        airdrop_repository.register_airdrop_window(airdrop_id=nunet_occam_airdrop.id, airdrop_window_name='Occam Window 1', description='Long description', registration_required=True,
                                                   registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)

    @patch('common.utils.recover_address')
    @patch('airdrop.infrastructure.repositories.user_registration_repo.UserRegistrationRepository.check_rewards_awarded')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_signature_for_airdrop_window_id')
    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.is_claimed_airdrop_window')
    def test_get_signature_for_airdrop_window_claim(self, mock_is_claimed_airdrop_window, mock_get_airdrop_window_claimable_info, mock_get_signature_for_airdrop_window_id, mock_check_rewards_awarded, mock_recover_address):

        address = '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'
        airdrop_claim_signature = '958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F'
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        mock_is_claimed_airdrop_window.return_value = {}
        mock_check_rewards_awarded.return_value = True, 1000
        mock_get_signature_for_airdrop_window_id.return_value = airdrop_claim_signature
        mock_get_airdrop_window_claimable_info.return_value = 100, address, contract_address, token_address,\
                                                              staking_contract_address,0

        mock_recover_address.return_value = address
        mock_check_rewards_awarded.value = True, 1000
        user_registration_payload = {
            "airdrop_window_id": str(airdrop_window_id),
            "airdrop_id": str(airdrop_id),
            "address": address,
            "signature": "958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F",
        }

        UserRegistrationServices().register(user_registration_payload)

        payload = {
            "address": address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_response = {'airdrop_id': str(airdrop_id), 'airdrop_window_id': str(airdrop_window_id),
                             'user_address': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8',
                             'signature': '958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F',
                             'claimable_amount': str(100),
                             'contract_address': '0x5e94577b949a56279637ff74dfcff2c28408f049',
                             'staking_contract_address': '0x5e94577b949a56279637ff74dfcff2c28408f049',
                             'token_address': '0x5e94577b949a56279637ff74dfcff2c28408f049',
                             'total_eligibility_amount':str(0)}

        status_code, result = AirdropServices().occam_airdrop_window_claim(payload)
        self.assertEqual(expected_response, result)

    def test_get_signature_for_airdrop_window_claim_with_invalid_windows(self):
        payload = {
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F442",
            "airdrop_id": airdrop_id,
            "airdrop_window_id": airdrop_window_id
        }

        status_code, result = AirdropServices().occam_airdrop_window_claim(payload)

        self.assertNotEqual(status_code, HTTPStatus.OK)

    def test_airdrop_window_claim_txn_status(self):

        payload = {
            "address": "0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8",
            "airdrop_id": airdrop_id,
            "airdrop_window_id": airdrop_window_id,
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

    def test_airdrop_event_consumer(self):

        payload = {
            "transactionHash": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "json_str": "{'authorizer': '0xD93209FDC420e8298bDFA3dBe340F366Faf1E7bc', 'claimer': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8', 'amount': 100, 'airDropId': 1, 'airDropWindowId': 1}",
            "event": "Claim"
        }

        event = {"data": payload}

        status, response = AirdropServices().airdrop_event_consumer(event)

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(response, {})

    def test_airdrop_event_consumer_with_airdropAmount_in_payload(self):

        payload = {
            "transactionHash": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "json_str": "{'authorizer': '0xD93209FDC420e8298bDFA3dBe340F366Faf1E7bc', 'claimer': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8', 'airDropAmount': 100, 'airDropId': 1, 'airDropWindowId': 1}",
            "event": "Claim"
        }

        event = {"data": payload}

        status, response = AirdropServices().airdrop_event_consumer(event)

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(response, {})

    def test_airdrop_event_consumer_with_duplicate_data(self):

        payload = {
            "transactionHash": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "json_str": "{'authorizer': '0xD93209FDC420e8298bDFA3dBe340F366Faf1E7bc', 'claimer': '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8', 'amount': 100, 'airDropId': 1, 'airDropWindowId': 1}",
            "event": "Claim"
        }

        event = {"data": payload}

        status, response = AirdropServices().airdrop_event_consumer(event)

        self.assertNotEqual(response, False)

    def test_airdrop_event_consumer_with_invalid_event(self):

        payload = {
            "transactionHash": "0x176133a958449C28930970989dB5fFFbEdd9F417",
            "json_str": "{'conversionAuthorizer': '0xD93209FDC420e8298bDFA3dBe340F366Faf1E7bc'}",
            "event": "NewAuthorizer"
        }

        event = {"data": payload}

        status, response = AirdropServices().airdrop_event_consumer(event)

        self.assertEqual(response, "Unsupported event")

    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_by_sending_full_rewards_to_wallet_if_stake_window_is_not_open(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = False
        is_user_can_stake = True
        window_max_stake = 100000
        window_stake_amount = 200
        max_stakable_amount = 10000
        already_staked_amount = 0
        airdrop_rewards = 20000

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake,window_stake_amount
        mock_get_stake_details_of_address.return_value = is_user_can_stake, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, \
                                                              contract_address, token_address, staking_contract_address,0

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(airdrop_rewards),
                "stakable_tokens": str(0),
                "is_stakable": False,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount": str(0)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_by_sending_full_rewards_to_wallet_as_user_exceeded_the_stake_limit(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_user_can_stake = True
        window_max_stake = 100000
        window_stake_amount = 200
        max_stakable_amount = 10000
        already_staked_amount = max_stakable_amount
        airdrop_rewards = 20000

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake,window_stake_amount
        mock_get_stake_details_of_address.return_value = is_user_can_stake, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, contract_address, token_address, staking_contract_address,0

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(airdrop_rewards),
                "stakable_tokens": str(0),
                "is_stakable": False,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount": str(0)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_by_partially_stake_and_claim(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_user_can_stake = True
        window_max_stake = 100000
        window_stake_amount = 200
        max_stakable_amount = 10000
        already_staked_amount = 5000
        airdrop_rewards = 10000

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake,window_stake_amount
        mock_get_stake_details_of_address.return_value = is_user_can_stake, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, contract_address, token_address, staking_contract_address,0

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(5000),
                "stakable_tokens": str(5000),
                "is_stakable": True,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount": str(0)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_by_full_rewards_staked(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_user_can_stake = True
        window_max_stake = 100000
        window_stake_amount = 200
        max_stakable_amount = 10000
        already_staked_amount = 0
        airdrop_rewards = 10000

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake,\
                                                     window_stake_amount
        mock_get_stake_details_of_address.return_value = is_user_can_stake, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address,\
                                                              contract_address, token_address, staking_contract_address,airdrop_rewards

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": "0",
                "stakable_tokens": str(airdrop_rewards),
                "is_stakable": True,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount":str(airdrop_rewards)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_if_airdrop_rewards_greater_than_max_stake_amount(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_user_can_stake = True
        window_max_stake = 100000
        window_stake_amount = 200
        max_stakable_amount = 10000
        already_staked_amount = 0
        airdrop_rewards = 50000

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake,window_stake_amount
        mock_get_stake_details_of_address.return_value = is_user_can_stake, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, contract_address, token_address, staking_contract_address,airdrop_rewards

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(40000),
                "stakable_tokens": str(10000),
                "is_stakable": True,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount": str(airdrop_rewards)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_user_can_stake_who_has_not_staked(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_already_staked_user = False
        window_max_stake = 100000
        window_stake_amount = 200
        max_stakable_amount = 10000
        already_staked_amount = 0
        airdrop_rewards = 10000

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake,window_stake_amount
        mock_get_stake_details_of_address.return_value = is_already_staked_user, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, contract_address,\
                                                              token_address, staking_contract_address,0

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(0),
                "stakable_tokens": str(10000),
                "is_stakable": True,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount": str(0)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_if_user_staked_max_amount_then_is_stakable_should_false(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_already_staked_user = True
        window_max_stake = 100000
        window_stake_amount = 200
        max_stakable_amount = 10000
        already_staked_amount = 10000
        airdrop_rewards = 1000

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake,window_stake_amount
        mock_get_stake_details_of_address.return_value = is_already_staked_user, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, contract_address, \
                                                              token_address, staking_contract_address,0

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(airdrop_rewards),
                "stakable_tokens": str(0),
                "is_stakable": False,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount": str(0)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)
    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_on_window_limit(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_user_can_stake = True
        window_max_stake = 10
        window_stake_amount = 9
        # => only 1 can be staked by any user
        max_stakable_amount = 5
        already_staked_amount = 1
        airdrop_rewards = 4
        # => ideally user can stake 4 if others had not staked,
        # but since the window has been filled by other users, this user can stake NOW only 1

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake, \
                                                     window_stake_amount
        mock_get_stake_details_of_address.return_value = is_user_can_stake, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, \
                                                              contract_address, token_address, staking_contract_address,airdrop_rewards

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(airdrop_rewards - min((window_max_stake - window_stake_amount),(max_stakable_amount-already_staked_amount))),
                "stakable_tokens": str(window_max_stake - window_stake_amount),
                "is_stakable": True,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount":str(airdrop_rewards)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_for_erroneous_stake_window(self, mock_get_stake_details_of_address,
                                                    mock_get_stake_window_details,
                                                    mock_get_airdrop_window_claimable_info):
        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_user_can_stake = True
        window_max_stake = 10
        window_stake_amount = 9
        # => only 1 can be staked by any user
        max_stakable_amount = 5
        # the amount already staked by this user is higher than the max limits
        already_staked_amount = 13
        airdrop_rewards = 4
        # => ideally user can stake 4 if others had not staked,
        # but since the window has been filled by other users, this user can stake NOW only 1

        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount, window_max_stake, \
                                                     window_stake_amount
        mock_get_stake_details_of_address.return_value = is_user_can_stake, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, \
                                                              contract_address, token_address, staking_contract_address, \
                                                              airdrop_rewards

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(airdrop_rewards),
                "stakable_tokens": str(0),
                "is_stakable": False,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount": str(airdrop_rewards)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)

    def test_airdrop_txn_watcher(self):

        response = AirdropServices().airdrop_txn_watcher()
        self.assertEqual(response, None)
    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_window_details')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_stake_details_of_address')
    def test_get_airdrop_window_stake_details_user_can_stake_but_amount_lessthan_minimum_stake_amount(self, mock_get_stake_details_of_address, mock_get_stake_window_details, mock_get_airdrop_window_claimable_info):

        user_wallet_address = "0x46EF7d49aaA68B29C227442BDbD18356415f8304"
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        is_stake_window_open = True
        is_already_staked_user = False
        window_max_stake = 100000
        window_stake_amount = 200
        max_stakable_amount = 10000
        already_staked_amount = 0
        airdrop_rewards = 10000
        AirdropRepository().update_minimum_stake_amount(airdrop_window_id,10001)


        mock_get_stake_window_details.return_value = is_stake_window_open, max_stakable_amount,window_max_stake,window_stake_amount
        mock_get_stake_details_of_address.return_value = is_already_staked_user, already_staked_amount
        mock_get_airdrop_window_claimable_info.return_value = airdrop_rewards, user_wallet_address, contract_address, \
                                                              token_address, staking_contract_address,0

        event = {
            "address": user_wallet_address,
            "airdrop_id": str(airdrop_id),
            "airdrop_window_id": str(airdrop_window_id)
        }

        expected_result = {
            "stake_details": {
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
                "address": user_wallet_address,
                "claimable_tokens_to_wallet": str(airdrop_rewards),
                "stakable_tokens": str(0),
                "is_stakable": False,
                "token_name": "AGIX",
                "airdrop_rewards": str(airdrop_rewards),
                "total_eligible_amount": str(0)
            }
        }

        status_code, response = AirdropServices().get_airdrop_window_stake_details(event)
        self.assertEqual(response, expected_result)
        self.assertEqual(status_code, HTTPStatus.OK.value)
        #reset the value
        AirdropRepository().update_minimum_stake_amount(airdrop_window_id,0)

