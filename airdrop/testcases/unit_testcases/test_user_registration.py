import unittest
from datetime import datetime, timedelta
from http import HTTPStatus
from eth_account import Account
from unittest import TestCase
from unittest.mock import Mock, patch

from airdrop.application.services.user_notification_service import \
    UserNotificationService
from airdrop.application.services.user_registration_services import \
    UserRegistrationServices
from airdrop.infrastructure.models import AirdropWindow, UserRegistration
from airdrop.infrastructure.repositories.airdrop_repository import \
    AirdropRepository
from airdrop.testcases.test_variables import AIRDROP
import secrets

class UserRegistration(TestCase):
    airdrop_id = None
    airdrop_window_id = None
    current_time = None

    def setUp(self):

        org_name = 'SINGNET'
        token_name = 'AGIX'
        token_type = 'CONTRACT'
        portal_link = 'https://ropsten-airdrop.singularitynet.io/'
        documentation_link = 'https://ropsten-airdrop.singularitynet.io/'
        description = 'This is a test airdrop'
        github_link = 'https://github.com/singnet/airdrop-services'
        global current_time
        current_time = datetime.utcnow()
        registration_start_date = datetime.utcnow() - timedelta(days=2)
        registration_end_date = datetime.utcnow() + timedelta(days=30)
        claim_start_date = datetime.utcnow() - timedelta(days=2)
        claim_end_date = datetime.utcnow() + timedelta(days=30)
        private_key = "0x" + secrets.token_hex(32)
        acct = Account.from_key(private_key)
        contract_address = acct.address
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        user_address = '0xCc3cD60FF9936B7C9272a649b24f290ADa562469'
        stakable_token_name = 'AGIX'

        now = datetime.utcnow()
        one_month_later = now + timedelta(days=30)
        registration_start_window = now - timedelta(days=2)
        stakable_token_name = 'AGIX'

        occam_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f048'
        occam_token_address = '0x5e94577b949a56279637ff74dfcff2c28408f048'
        occam_user_address = '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'
        occam_stakable_token_name = 'AGIX'

        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link, stakable_token_name)
        airdrop_window= airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id, airdrop_window_name='Airdrop Window 1', description='Long description', registration_required=True,
                                                   registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)
        global airdrop_id
        airdrop_id = airdrop.id
        global airdrop_window_id
        airdrop_window_id = airdrop_window.id
        nunet_occam_airdrop = airdrop_repository.register_airdrop(
            occam_token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link, occam_stakable_token_name)
        airdrop_repository.register_airdrop_window(airdrop_id=nunet_occam_airdrop.id, airdrop_window_name='Occam Window 1', description='Long description', registration_required=True,
                                                   registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)

    @patch('common.utils.recover_address')
    @patch('airdrop.infrastructure.repositories.user_repository.UserRepository.check_rewards_awarded')
    @patch("airdrop.application.services.user_registration_services.UserRegistrationServices.get_secret_key_for_receipt")
    def test_user_registration(self, mock_get_secret_key_for_receipt,mock_check_rewards_awarded, mock_recover_address):
        address = '0x765C9E1BCa00002e294c9aa9dC3F96C2a022025C'
        private_key = '12b7972e86b2f45f130a3089ff1908d00d8fed70dc9b7b002c6656d983776001'
        mock_get_secret_key_for_receipt.return_value = private_key
        mock_recover_address.return_value = address
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        mock_check_rewards_awarded.value = True, 1000
        registration_start_date = datetime.utcnow() - timedelta(days=2)
        registration_end_date = datetime.utcnow() + timedelta(days=30)
        claim_start_date = datetime.utcnow() - timedelta(days=2)
        claim_end_date = datetime.utcnow() + timedelta(days=30)
        airdrop_ = AirdropRepository().register_airdrop(
            token_address, "org", "tkanme", "NA", contract_address, "", "", "", "", "")
        airdrop_window_= AirdropRepository().register_airdrop_window(airdrop_id=airdrop_.id, airdrop_window_name=str(datetime.utcnow()), description='reg Long description', registration_required=True,
                                                               registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)

        inputs = {
            "airdrop_window_id": str(airdrop_window_.id),
            "airdrop_id": str(airdrop_.id),
            "address": address,
            "signature": "958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F",
        }
        status, response = UserRegistrationServices().register(inputs)
        self.assertEqual(status, HTTPStatus.OK)

    @patch('common.utils.recover_address')
    @patch('airdrop.infrastructure.repositories.user_repository.UserRepository.check_rewards_awarded')
    def test_attempt_reregistration(self, mock_check_rewards_awarded, mock_recover_address):
        address = '0x176133a958449C28930970989dB5fFFbEdd9F448'
        mock_recover_address.return_value = address
        mock_check_rewards_awarded.value = True, 1000
        inputs = {
            "airdrop_window_id": str(airdrop_id),
            "airdrop_id": str(airdrop_window_id),
            "address": address,
            "signature": "958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F",
        }
        status = UserRegistrationServices().register(inputs)
        self.assertNotEqual(status, HTTPStatus.OK)

    def test_airdrop_window_user_eligibility(self):
        inputs = {
            "airdrop_window_id": str(airdrop_window_id),
            "airdrop_id": str(airdrop_id),
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F448",
            "signature": "958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F",
        }
        status, response = UserRegistrationServices().eligibility(inputs)
        self.assertEqual(status, HTTPStatus.OK)

    def test_airdrop_window_user_eligibility_with_invalid_info(self):
        inputs = {
            "airdrop_window_id": "100",
            "airdrop_id": "100",
            "address": "0x176133a958449C28930970989dB5fFFbEdd9F448",
            "signature": "958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F",
        }
        status = UserRegistrationServices().eligibility(inputs)
        self.assertNotEqual(status, HTTPStatus.OK)

    def test_user_notification_subscription(self):

        payload = {
            "email": str(airdrop_id)+"email@provider.com",
            "airdrop_id": airdrop_id,
        }
        status, response = UserNotificationService().subscribe_to_notifications(payload)
        self.assertEqual(response, HTTPStatus.OK.phrase)

        status, response = UserNotificationService().subscribe_to_notifications(payload)
        self.assertNotEqual(response, HTTPStatus.OK.phrase)


