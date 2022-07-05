import json
from unittest import TestCase
from unittest.mock import patch

from py_eth_sig_utils.signing import v_r_s_to_signature, sign_typed_data

from airdrop.application.handlers.airdrop_handlers import user_eligibility, user_registration
from airdrop.constants import USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT
from airdrop.testcases.functional_testcases.nunet_airdrop_test_data import NuNetAirdropData, \
    NuNetAirdropWindow1Data, NuNetAirdropWindow2Data, NuNetAirdropUser1, \
    SECRETS_MANAGER_MOCK_VALUE
from airdrop.testcases.functional_testcases.load_test_data import clear_database, load_airdrop_data, \
    load_airdrop_window_data, load_user_reward_data, load_airdrop_user_registration


class TestNuNetAirdropServices(TestCase):
    def setUp(self):
        clear_database()
        self.airdrop = load_airdrop_data(NuNetAirdropData)
        self.nunet_airdrop_window1 = load_airdrop_window_data(self.airdrop.id, NuNetAirdropWindow1Data)
        self.nunet_airdrop_window2 = load_airdrop_window_data(self.airdrop.id, NuNetAirdropWindow2Data)

    @patch("common.boto_utils.BotoUtils.get_parameter_value_from_secrets_manager")
    def test_nunet_airdrop_user_registration(self, mock_get_parameter_value_from_secrets_manager):
        mock_get_parameter_value_from_secrets_manager.return_value = SECRETS_MANAGER_MOCK_VALUE
        formatted_message = USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT
        formatted_message["message"] = {
            "Airdrop": {
                "airdropId": self.airdrop.id,
                "airdropWindowId": self.nunet_airdrop_window1.id,
                "blockNumber": NuNetAirdropUser1.signature_details["block_no"],
                "walletAddress": NuNetAirdropUser1.address
            }
        }
        formatted_message["domain"]["name"] = NuNetAirdropUser1.signature_details["domain_name"]
        signature = v_r_s_to_signature(*sign_typed_data(formatted_message, NuNetAirdropUser1.private_key)).hex()
        event = {
            "body": json.dumps({
                "address": NuNetAirdropUser1.address,
                "airdrop_id": self.airdrop.id,
                "airdrop_window_id": self.nunet_airdrop_window1.id,
                "signature": signature,
                "block_number": NuNetAirdropUser1.signature_details["block_no"]
            })
        }
        response = user_registration(event=event, context=None)
        print(response)
        assert (response["statusCode"] == 400)
        response_body = json.loads(response["body"])
        assert (response_body["error"]["message"] == "Exception('Address is not eligible for this airdrop.')")

        load_user_reward_data(self.airdrop.id, self.nunet_airdrop_window1.id, NuNetAirdropUser1)
        response = user_registration(event=event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        print(response_body)
        assert (len(response_body["data"]) > 0)

    def test_nunet_airdrop_user_eligibility(self):
        clear_database()
        self.setUp()
        event = {
            "body": json.dumps({
                "address": NuNetAirdropUser1.address,
                "airdrop_id": self.airdrop.id,
                "airdrop_window_id": self.nunet_airdrop_window1.id
            })
        }
        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertFalse(response_body["data"]["is_eligible"])
        self.assertFalse(response_body["data"]["is_already_registered"])
        assert (response_body["data"]["airdrop_window_rewards"] == 0)
        self.assertDictEqual(response_body["data"]["registration_details"], {})

        load_user_reward_data(self.airdrop.id, self.nunet_airdrop_window1.id, NuNetAirdropUser1)
        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertTrue(response_body["data"]["is_eligible"])
        self.assertDictEqual(response_body["data"]["registration_details"], {})

        load_airdrop_user_registration(self.nunet_airdrop_window1.id, NuNetAirdropUser1)
        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertTrue(response_body["data"]["is_eligible"])
        assert (len(response_body["data"]["registration_details"]) > 2)

        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertTrue(response_body["data"]["is_already_registered"])

    def tearDown(self):
        clear_database()