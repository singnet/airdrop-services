import unittest
import json
from unittest.mock import patch
from http import HTTPStatus
from datetime import datetime, timedelta
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.application.handlers.airdrop_handlers import get_airdrop_schedules, user_eligibility, user_registration, airdrop_window_claims, airdrop_window_claim_status, user_notifications
from airdrop.infrastructure.models import UserRegistration,Airdrop,AirdropWindow,UserReward,ClaimHistory,UserNotifications


class TestAirdropHandler(unittest.TestCase):
    airdrop_id = None
    airdrop_window_id = None
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
        global airdrop_id
        airdrop_id = airdrop.id
        airdrop_windows = airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id, airdrop_window_name='Airdrop Window 1', description='Long description', registration_required=True,
                                                   registration_start_period=registration_start_date, registration_end_period=registration_end_date, snapshot_required=True, claim_start_period=claim_start_date, claim_end_period=claim_end_date, total_airdrop_tokens=1000000)
        global airdrop_window_id
        airdrop_window_id = airdrop_windows.id
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
       
        event = {
            "body": json.dumps({
                "address": address,
                "airdrop_id": str(airdrop_id),
                "airdrop_window_id": str(airdrop_window_id),
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

    def test_fetch_total_eligibility_amount(self):
        #delete it all !!!!
        AirdropRepository().session.query(ClaimHistory).delete()
        AirdropRepository().session.query(UserRegistration).delete()
        AirdropRepository().session.query(UserReward).delete()
        AirdropRepository().session.query(AirdropWindow).delete()
        AirdropRepository().session.query(Airdrop).delete()
        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            "0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8", "TEST", "TEST", "token_type",
            "0x2fc8ae60108765056ff63a07843a5b7ec9ff89ef", "portal_link",
            "documentation_link",
            "description", "github_link", "stakable_token_name")
        registration_start_date = datetime.utcnow() - timedelta(days=2)
        registration_end_date = datetime.utcnow() + timedelta(days=30)
        claim_start_date = datetime.utcnow() - timedelta(days=5)
        claim_end_date = datetime.utcnow() + timedelta(days=30)

        airdrop_window1 = airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id,
                                                                     airdrop_window_name='Airdrop Window 1',
                                                                     description='Long description',
                                                                     registration_required=True,
                                                                     registration_start_period=registration_start_date,
                                                                     registration_end_period=registration_end_date,
                                                                     snapshot_required=True,
                                                                     claim_start_period=claim_start_date,
                                                                     claim_end_period=claim_end_date,
                                                                     total_airdrop_tokens=1000000)
        airdrop_window2 = airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id,
                                                                     airdrop_window_name='Airdrop Window 2',
                                                                     description='Long description',
                                                                     registration_required=True,
                                                                     registration_start_period=registration_start_date,
                                                                     registration_end_period=registration_end_date,
                                                                     snapshot_required=True,
                                                                     claim_start_period=datetime.utcnow() - timedelta(days=2),
                                                                     claim_end_period=claim_end_date,
                                                                     total_airdrop_tokens=1000000)

        airdrop_window3 = airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id,
                                                                     airdrop_window_name='Airdrop Window 3',
                                                                     description='Long description',
                                                                     registration_required=True,
                                                                     registration_start_period=registration_start_date,
                                                                     registration_end_period=registration_end_date,
                                                                     snapshot_required=True,
                                                                     claim_start_period=datetime.utcnow() + timedelta(
                                                                         days=20),
                                                                     claim_end_period=datetime.utcnow() + timedelta(
                                                                         days=25),
                                                                     total_airdrop_tokens=1000000)

        #now user has rewards for all three windows
        airdrop_repository.register_user_rewards(airdrop.id,airdrop_window1.id,100,
                                                 '0xCc3cD60FF9936B7C9272a649b24f290ADa562469',1,1)
        airdrop_repository.register_user_rewards(airdrop.id, airdrop_window2.id, 100,
                                                 '0xCc3cD60FF9936B7C9272a649b24f290ADa562469',1,1)
        airdrop_repository.register_user_rewards(airdrop.id, airdrop_window3.id, 100,
                                                 '0xCc3cD60FF9936B7C9272a649b24f290ADa562469',1,1)

        #User has not registered for any window
        result = airdrop_repository.fetch_total_eligibility_amount(airdrop.id,
                                                                   '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')
        self.assertEqual(result,0)

        # User has registered for the first window
        airdrop_repository.register_user_registration(airdrop_window1.id,'0xCc3cD60FF9936B7C9272a649b24f290ADa562469')
        result = airdrop_repository.fetch_total_eligibility_amount(airdrop.id,
                                                                   '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')

        # User has registrations for the third window,but claim is not yet open for this window
        # hence this window should never be considered , total eligbile amount is applicable only for past claim
        # or acitve claim windows
        airdrop_repository.register_user_registration(airdrop_window3.id, '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')
        result = airdrop_repository.fetch_total_eligibility_amount(airdrop.id,
                                                                   '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')
        self.assertEqual(result, 100)


        # User has registrations for the 2nd window which is active
        airdrop_repository.register_user_registration(airdrop_window2.id, '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')
        result = airdrop_repository.fetch_total_eligibility_amount(airdrop.id,
                                                                   '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')
        self.assertEqual(result, 200)

        #assuming no claim has happend til now , total_rewards user can claim = 200
        rewards_for_claim_raw = airdrop_repository.fetch_total_rewards_amount(airdrop.id,
                                                                   '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')

        self.assertEqual(200, rewards_for_claim_raw[0]['total_rewards'])


        #make an entry in the claim table for window 2 => all amount till this point has been claimed
        #hence rewards to be claimed is zero for current time  , however total eligibility was always 200
        airdrop_repository.register_claim_history(airdrop.id,airdrop_window2.id,
                                                  '0xCc3cD60FF9936B7C9272a649b24f290ADa562469',200,0,'PENDING',
                                                  'transaction_hash')
        rewards_for_claim_raw = airdrop_repository.fetch_total_rewards_amount(airdrop.id,
                                                                              '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')
        self.assertEqual(None, rewards_for_claim_raw[0]['total_rewards'])


    def tearDown(self):
        self.assertEqual(100, 100)
        AirdropRepository().session.query(ClaimHistory).delete()
        AirdropRepository().session.query(UserRegistration).delete()
        AirdropRepository().session.query(UserReward).delete()
        AirdropRepository().session.query(AirdropWindow).delete()
        AirdropRepository().session.query(Airdrop).delete()


if __name__ == '__main__':
    unittest.main()
