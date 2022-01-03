import unittest
import json
from unittest.mock import patch
from http import HTTPStatus
from datetime import datetime, timedelta
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.application.handlers.airdrop_handlers import get_airdrop_schedules, user_eligibility, user_registration, airdrop_window_claims, airdrop_window_claim_status, user_notifications
from airdrop.infrastructure.models import UserRegistration


class TestAirdropHandler(unittest.TestCase):
    def setUp(self):
        self.tearDown()
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
        now = datetime.utcnow()

        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        user_address = '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'
        stakable_token_name = 'AGIX'

        occam_contract_address = '0x6e94577b949a56279637ff74dfcff2c28408f049'
        occam_token_address = '0x5e93577b949a56279637ff74dfcff2c28408f049'
        occam_user_address = '0xEA6741dDe714fd979de3EdF0F56AA9716B898ec8'
        occam_stakable_token_name = 'AGIX'

        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link, stakable_token_name)
        airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id, airdrop_window_name='Airdrop Window 1', description='Long description', registration_required=True,
                                                   registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)

        nunet_occam_airdrop = airdrop_repository.register_airdrop(
            occam_token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link, occam_stakable_token_name)
        airdrop_repository.register_airdrop_window(airdrop_id=nunet_occam_airdrop.id, airdrop_window_name='Occam Window 1', description='Long description', registration_required=True,
                                                   registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)

    @patch("common.utils.Utils.report_slack")
    def test_get_airdrop_schedules(self, mock_report_slack):
        event = {
            "pathParameters": {
                "token_address": "0x5e94577b949a56279637ff74dfcff2c28408f049"
            }
        }
        result = get_airdrop_schedules(event, None)
        airdrop_schedules = result['body']
        self.assertIsNotNone(airdrop_schedules)

    @patch("common.utils.Utils.report_slack")
    def test_get_airdrop_window_eligibility(self, mock_report_slack):
        address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        airdrop_window_id = "1"
        airdrop_id = "1"
        event = {
            "body": json.dumps({
                "address": address,
                "airdrop_id": airdrop_id,
                "airdrop_window_id": airdrop_window_id
            })
        }
        result = user_eligibility(event, None)
        result = json.loads(result['body'])
        user_eligibility_object = result['data']
        self.assertIn(user_eligibility_object['is_eligible'], [True, False])
        self.assertIn(
            user_eligibility_object['is_already_registered'], [True, False])
        self.assertIn(
            user_eligibility_object['is_airdrop_window_claimed'], [True, False])
        self.assertEqual(user_eligibility_object['user_address'], address)
        self.assertEqual(user_eligibility_object['airdrop_id'], airdrop_id)
        self.assertEqual(
            user_eligibility_object['airdrop_window_id'], airdrop_window_id)

    @patch("common.utils.Utils.report_slack")
    @patch('common.utils.recover_address')
    def test_get_airdrop_window_user_registration(self, mock_recover_address, mock_report_slack):
        address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        mock_recover_address.return_value = address
        airdrop_window_id = "1"
        airdrop_id = "1"
        event = {
            "body": json.dumps({
                "address": address,
                "airdrop_id": airdrop_id,
                "airdrop_window_id": airdrop_window_id,
                "signature": "9e05e94577b949a56279637ff74dfcff2c28408f049"
            })
        }
        result = user_registration(event, None)
        result = json.loads(result['body'])
        self.assertEqual(result['status'], HTTPStatus.OK.value)

    @patch("common.utils.Utils.report_slack")
    @patch('common.utils.recover_address')
    @patch('airdrop.infrastructure.repositories.user_repository.UserRepository.check_rewards_awarded')
    @patch('airdrop.application.services.airdrop_services.AirdropServices.get_signature_for_airdrop_window_id')
    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.get_airdrop_window_claimable_info')
    @patch('airdrop.infrastructure.repositories.airdrop_repository.AirdropRepository.is_claimed_airdrop_window')
    def test_airdrop_window_claim(self, mock_is_claimed_airdrop_window, mock_get_airdrop_window_claimable_info, mock_get_signature_for_airdrop_window_id, mock_check_rewards_awarded, mock_recover_address, mock_report_slack):
        address = '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'
        airdrop_claim_signature = '958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F'
        contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        token_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'
        staking_contract_address = '0x5e94577b949a56279637ff74dfcff2c28408f049'

        mock_recover_address.return_value = address
        mock_is_claimed_airdrop_window.return_value = {}
        mock_check_rewards_awarded.return_value = True, 1000
        mock_get_signature_for_airdrop_window_id.return_value = airdrop_claim_signature
        mock_get_airdrop_window_claimable_info.return_value = 100, address, contract_address, token_address, staking_contract_address

        mock_recover_address.return_value = address
        mock_check_rewards_awarded.value = True, 1000
        airdrop_window_id = "1"
        airdrop_id = "1"
        event = {
            "body": json.dumps({
                "address": address,
                "airdrop_id": airdrop_id,
                "airdrop_window_id": airdrop_window_id,
                "signature": "9e05e94577b949a56279637ff74dfcff2c28408f049",
                "token_address": token_address,
                "contract_address": contract_address,
                "staking_contract_address": staking_contract_address
            })
        }
        result = airdrop_window_claims(event, None)
        result = json.loads(result['body'])
        claim_signature_object = result['data']
        self.assertEqual(result['status'], HTTPStatus.OK.value)
        self.assertEqual(claim_signature_object['user_address'], address)

    @patch("common.utils.Utils.report_slack")
    def test_airdrop_window_claim_update_txn(self,  mock_report_slack):
        address = '0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8'
        airdrop_claim_signature = '958449C28930970989dB5fFFbEdd9F44989d33a958B5fF989dB5f33a958F'

        airdrop_window_id = "1"
        airdrop_id = "1"
        event = {
            "body": json.dumps({
                "address": address,
                "airdrop_id": airdrop_id,
                "airdrop_window_id": airdrop_window_id,
                "amount": "100",
                "txn_hash": "9e05e94577b949a56279637ff74dfcff2c28408f049"
            })
        }
        result = airdrop_window_claim_status(event, None)
        result = json.loads(result['body'])
        self.assertIsNotNone(result)

    @patch("common.utils.Utils.report_slack")
    def test_user_notifications(self,  mock_report_slack):
        event = {
            "body": json.dumps({
                "email": "mail@provider.com"
            })
        }
        result = user_notifications(event, None)
        result = json.loads(result['body'])
        self.assertIsNotNone(result)

    def tearDown(self):
        AirdropRepository().session.query(UserRegistration).delete()


if __name__ == '__main__':
    unittest.main()
