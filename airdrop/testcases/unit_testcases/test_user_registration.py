import unittest
from datetime import datetime, timedelta
from http import HTTPStatus
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


class UserRegistration(TestCase):

    def setUp(self):

        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        user_address = '0xCc3cD60FF9936B7C9272a649b24f290ADa562469'

        now = datetime.utcnow()
        one_month_later = now + timedelta(days=30)
        registration_start_window = now - timedelta(days=2)

        airdrop_repo = AirdropRepository()
        airdrop = airdrop_repo.register_airdrop(
            address=token_address, org_name='SINGNET', token_name='AGIX', token_type='Contract', contract_address=contract_address, portal_link='https://beta.singularitynet.io', documentation_link='https://beta.singularitynet.io', github_link_for_contract='https://github.com/singnet', description='Long description')

        airdrop_repo.register_airdrop_window(airdrop_id=airdrop.id, airdrop_window_name='Airdrop Window 1', description='Long description', registration_required=True,
                                             registration_start_period=registration_start_window, registration_end_period=one_month_later, snapshot_required=True, claim_start_period=now, claim_end_period=one_month_later, total_airdrop_tokens=1000000)

    @patch('common.utils.recover_address')
    @patch('airdrop.infrastructure.repositories.user_repository.UserRepository.check_rewards_awarded')
    def test_user_registration(self, mock_check_rewards_awarded, mock_recover_address):
        address = '0x176133a958449C28930970989dB5fFFbEdd9F448'
        mock_recover_address.return_value = address
        mock_check_rewards_awarded.value = True, 1000
        inputs = {
            "airdrop_window_id": "1",
            "airdrop_id": "1",
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
            "airdrop_window_id": "1",
            "airdrop_id": "1",
            "address": address,
            "signature": "958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F",
        }
        status = UserRegistrationServices().register(inputs)
        self.assertNotEqual(status, HTTPStatus.OK)

    def test_airdrop_window_user_eligibility(self):
        inputs = {
            "airdrop_window_id": "1",
            "airdrop_id": "1",
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
            "email": "email@provider.com",
        }
        status, response = UserNotificationService().subscribe_to_notifications(payload)
        self.assertEqual(response, HTTPStatus.OK.phrase)

    def test_user_notification_subscription_with_existing_email(self):
        payload = {
            "email": "email@provider.com",
        }
        status, response = UserNotificationService().subscribe_to_notifications(payload)
        self.assertNotEqual(response, HTTPStatus.OK.phrase)
