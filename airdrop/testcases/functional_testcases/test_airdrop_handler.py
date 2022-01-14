import unittest
import json
import web3
from web3 import Web3
from eth_account.messages import defunct_hash_message, encode_defunct
from airdrop.config import NETWORK
from unittest.mock import patch
from http import HTTPStatus
from datetime import datetime, timedelta
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.application.handlers.airdrop_handlers import get_airdrop_schedules, user_eligibility, user_registration, \
    airdrop_window_claims, airdrop_window_claim_status, user_notifications, airdrop_window_secured_claims
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
        mock_get_airdrop_window_claimable_info.return_value = 100, address, contract_address, token_address, staking_contract_address,0

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

    @patch("common.boto_utils.BotoUtils.get_parameter_value_from_secrets_manager")
    def test_nunet_occam_signature(self,  mock_get_parameter_value_from_secrets_manager):
        user_address = "0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10"
        token_address = "0x765C9E1BCa00002e294c9aa9dC3F96C2a022025C"
        contract_address = "0xFb4D686B3330893d6af6F996AB325f8ea26c949E"
        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            token_address, "TEST_ORG", "TEST_TOKEN_NAME", "token_type",
            contract_address, "portal_link",
            "documentation_link",
            "description", "github_link", "stakable_token_name")
        registration_start_date = datetime.utcnow() - timedelta(days=2)
        registration_end_date = datetime.utcnow() + timedelta(days=30)
        claim_start_date = datetime.utcnow() - timedelta(days=5)
        claim_end_date = datetime.utcnow() + timedelta(days=30)

        airdrop_window = airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id,
                                                                     airdrop_window_name='TEST_ORG-Airdrop Window 1',
                                                                     description='Long description',
                                                                     registration_required=True,
                                                                     registration_start_period=registration_start_date,
                                                                     registration_end_period=registration_end_date,
                                                                     snapshot_required=True,
                                                                     claim_start_period=claim_start_date,
                                                                     claim_end_period=claim_end_date,
                                                                     total_airdrop_tokens=1000000)
        private_key = '12b7972e86b2f45f130a3089ff1908d00d8fed70dc9b7b002c6656d983776001'
        mock_get_parameter_value_from_secrets_manager.return_value = private_key
        event = {
            "body": json.dumps({
                "address": "0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10",
                "airdrop_id": str(airdrop.id),
                "airdrop_window_id": str(airdrop_window.id),
            })
        }
        #add rewards for this user in the active window, take a very large number so that we support
        reward = 10000000000000000000000
        airdrop_repository.register_user_rewards(airdrop.id, airdrop_window.id, reward,
                                                 '0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10', 1, 1)
        # Register the user for the window
        airdrop_repository.register_user_registration(airdrop_window.id, '0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10')

        #now generate the expected signature
        user_address = Web3.toChecksumAddress(user_address)
        token_address = Web3.toChecksumAddress(token_address)
        contract_address = Web3.toChecksumAddress(contract_address)
        big_reward = '1e+22'
        print("int of big_reward",str(reward))
        print("Generate claim signature user_address: ", user_address)
        print("Generate claim signature token_address: ", token_address)
        print("Generate claim signature contract_address: ", contract_address)

        message = web3.Web3.soliditySha3(
            ["string", "uint256", "address", "uint256",
             "uint256", "address", "address"],
            ["__airdropclaim", int(reward), user_address, int(airdrop.id),
             int(airdrop_window.id), contract_address, token_address],
        )

        message_hash = encode_defunct(message)

        web3_object = Web3(web3.providers.HTTPProvider(
            NETWORK['http_provider']))
        signed_message = web3_object.eth.account.sign_message(
            message_hash, private_key=private_key)

        expected_signature = signed_message.signature.hex()
        expected_response = {'airdrop_id': str(airdrop.id), 'airdrop_window_id': str(airdrop_window.id),
                             'user_address': '0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10',
                             'signature': expected_signature,
                             'claimable_amount': str(reward),
                             'contract_address': '0xFb4D686B3330893d6af6F996AB325f8ea26c949E',
                             'staking_contract_address': None,
                             'token_address': '0x765C9E1BCa00002e294c9aa9dC3F96C2a022025C',
                             'total_eligibility_amount': str(reward)}
        result = airdrop_window_claims(event, None)
        result = json.loads(result['body'])
        final_result = result['data']
        self.assertEqual(expected_response,final_result )

    @patch("common.boto_utils.BotoUtils.get_parameter_value_from_secrets_manager")
    def test_airdrop_signature(self,  mock_get_parameter_value_from_secrets_manager):
        user_address = "0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10"
        token_address = "0x765C9E1BCa00002e294c9aa9dC3F96C2a022025C"
        contract_address = "0xFb4D686B3330893d6af6F996AB325f8ea26c949E"
        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            token_address, "TEST_ORG", "TEST_TOKEN_NAME", "token_type",
            contract_address, "portal_link",
            "documentation_link",
            "description", "github_link", "stakable_token_name")
        registration_start_date = datetime.utcnow() - timedelta(days=2)
        registration_end_date = datetime.utcnow() + timedelta(days=30)
        claim_start_date = datetime.utcnow() - timedelta(days=5)
        claim_end_date = datetime.utcnow() + timedelta(days=30)

        airdrop_window = airdrop_repository.register_airdrop_window(airdrop_id=airdrop.id,
                                                                     airdrop_window_name='TEST_ORG-Airdrop Window 1',
                                                                     description='Long description',
                                                                     registration_required=True,
                                                                     registration_start_period=registration_start_date,
                                                                     registration_end_period=registration_end_date,
                                                                     snapshot_required=True,
                                                                     claim_start_period=claim_start_date,
                                                                     claim_end_period=claim_end_date,
                                                                     total_airdrop_tokens=1000000)
        private_key = '12b7972e86b2f45f130a3089ff1908d00d8fed70dc9b7b002c6656d983776001'
        mock_get_parameter_value_from_secrets_manager.return_value = private_key
        event = {
            "body": json.dumps({
                "address": "0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10",
                "airdrop_id": str(airdrop.id),
                "airdrop_window_id": str(airdrop_window.id),
            })
        }
        #add rewards for this user in the active window
        airdrop_repository.register_user_rewards(airdrop.id, airdrop_window.id, 150,
                                                 '0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10', 1, 1)
        # Register the user for the window
        airdrop_repository.register_user_registration(airdrop_window.id, '0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10')

        #now generate the expected signature
        user_address = Web3.toChecksumAddress(user_address)
        token_address = Web3.toChecksumAddress(token_address)
        contract_address = Web3.toChecksumAddress(contract_address)

        print("Generate claim signature user_address: ", user_address)
        print("Generate claim signature token_address: ", token_address)
        print("Generate claim signature contract_address: ", contract_address)

        message = web3.Web3.soliditySha3(
            ["string", "uint256","uint256", "address", "uint256",
             "uint256", "address", "address"],
            ["__airdropclaim", int(150),int(150), user_address, int(airdrop.id),
             int(airdrop_window.id), contract_address, token_address],
        )

        message_hash = encode_defunct(message)

        web3_object = Web3(web3.providers.HTTPProvider(
            NETWORK['http_provider']))
        signed_message = web3_object.eth.account.sign_message(
            message_hash, private_key=private_key)

        expected_signature = signed_message.signature.hex()
        expected_response = {'airdrop_id': str(airdrop.id), 'airdrop_window_id': str(airdrop_window.id),
                             'user_address': '0x164096A3878DEd9C2A30c85D9c4b713d5305Ab10',
                             'signature': expected_signature,
                             'claimable_amount': '150',
                             'contract_address': '0xFb4D686B3330893d6af6F996AB325f8ea26c949E',
                             'staking_contract_address': None,
                             'token_address': '0x765C9E1BCa00002e294c9aa9dC3F96C2a022025C',
                             'total_eligibility_amount': '150'}
        result = airdrop_window_secured_claims(event, None)
        result = json.loads(result['body'])
        final_result = result['data']
        self.assertEqual(expected_response,final_result )

    def test_fetch_total_eligibility_amount(self):
        #delete it all !!!!
        AirdropRepository().session.query(ClaimHistory).delete()
        AirdropRepository().session.query(UserRegistration).delete()
        AirdropRepository().session.query(UserReward).delete()
        AirdropRepository().session.query(AirdropWindow).delete()
        AirdropRepository().session.query(Airdrop).delete()
        airdrop_repository = AirdropRepository()
        airdrop = airdrop_repository.register_airdrop(
            "0x5e94577b949a56279637ff74dfcff2c28408f049", "TEST_ORG", "TEST_TOKEN_NAME", "token_type",
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
        rewards_for_claim = airdrop_repository.fetch_total_rewards_amount(airdrop.id,
                                                                   '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')

        self.assertEqual(200, rewards_for_claim)


        #make an entry in the claim table for window 2 => all amount till this point has been claimed
        #hence rewards to be claimed is zero for current time  , however total eligibility was always 200
        airdrop_repository.register_claim_history(airdrop.id,airdrop_window2.id,
                                                  '0xCc3cD60FF9936B7C9272a649b24f290ADa562469',200,0,'PENDING',
                                                  'transaction_hash')
        rewards_for_claim = airdrop_repository.fetch_total_rewards_amount(airdrop.id,
                                                                              '0xCc3cD60FF9936B7C9272a649b24f290ADa562469')
        self.assertEqual(0, rewards_for_claim)


    def tearDown(self):
        self.assertEqual(100, 100)
        AirdropRepository().session.query(ClaimHistory).delete()
        AirdropRepository().session.query(UserRegistration).delete()
        AirdropRepository().session.query(UserReward).delete()
        AirdropRepository().session.query(AirdropWindow).delete()
        AirdropRepository().session.query(Airdrop).delete()


if __name__ == '__main__':
    unittest.main()
