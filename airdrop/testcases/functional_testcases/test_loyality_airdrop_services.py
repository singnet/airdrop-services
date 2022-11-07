import json
from unittest import TestCase
from unittest.mock import patch

from py_eth_sig_utils.signing import v_r_s_to_signature, sign_typed_data

from airdrop.application.handlers.airdrop_handlers import user_eligibility, user_registration, airdrop_window_claim
from airdrop.constants import USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT
from airdrop.testcases.functional_testcases.load_test_data import clear_database, load_airdrop_data, \
    load_airdrop_window_data, load_user_reward_data, load_airdrop_user_registration
from airdrop.testcases.functional_testcases.loyalty_airdrop_test_data import LoyaltyAirdropData, \
    LoyaltyAirdropWindow1Data, LoyaltyAirdropWindow2Data, LoyaltyAirdropUser1, \
    SECRETS_MANAGER_MOCK_VALUE


class TestLoyaltyAirdropServices(TestCase):
    def setUp(self):
        clear_database()
        self.airdrop = load_airdrop_data(LoyaltyAirdropData)
        self.loyalty_airdrop_window1 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow1Data)
        self.loyalty_airdrop_window2 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow2Data)

    @patch("common.boto_utils.BotoUtils.get_parameter_value_from_secrets_manager")
    def test_loyalty_airdrop_user_registration(self, mock_get_parameter_value_from_secrets_manager):
        mock_get_parameter_value_from_secrets_manager.return_value = SECRETS_MANAGER_MOCK_VALUE
        formatted_message = USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT
        formatted_message["message"] = {
            "Airdrop": {
                "airdropId": self.airdrop.id,
                "airdropWindowId": self.loyalty_airdrop_window1.id,
                "blockNumber": LoyaltyAirdropUser1.signature_details["block_no"],
                "walletAddress": LoyaltyAirdropUser1.address,
                "cardanoAddress": LoyaltyAirdropUser1.cardano_address,
                "cardanoWalletName": LoyaltyAirdropUser1.cardano_wallet_name
            }
        }
        formatted_message["domain"]["name"] = LoyaltyAirdropUser1.signature_details["domain_name"]
        signature = v_r_s_to_signature(*sign_typed_data(formatted_message, LoyaltyAirdropUser1.private_key)).hex()
        event = {
            "body": json.dumps({
                "address": LoyaltyAirdropUser1.address,
                "cardano_address": LoyaltyAirdropUser1.cardano_address,
                "cardano_wallet_name": LoyaltyAirdropUser1.cardano_wallet_name,
                "airdrop_id": self.airdrop.id,
                "airdrop_window_id": self.loyalty_airdrop_window1.id,
                "signature": signature,
                "block_number": LoyaltyAirdropUser1.signature_details["block_no"]
            })
        }
        response = user_registration(event=event, context=None)
        assert (response["statusCode"] == 400)
        response_body = json.loads(response["body"])
        assert (response_body["error"]["message"] == "Exception('Address is not eligible for this airdrop.')")

        load_user_reward_data(self.airdrop.id, self.loyalty_airdrop_window1.id, LoyaltyAirdropUser1)
        response = user_registration(event=event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert (len(response_body["data"]) == 2)

    def test_loyalty_airdrop_user_eligibility_case1(self):
        clear_database()
        self.setUp()
        event = {
            "body": json.dumps({
                "address": LoyaltyAirdropUser1.address,
                "airdrop_id": self.airdrop.id,
                "airdrop_window_id": self.loyalty_airdrop_window1.id
            })
        }
        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertFalse(response_body["data"]["is_eligible"])
        self.assertFalse(response_body["data"]["is_already_registered"])
        assert (response_body["data"]["airdrop_window_rewards"] == 0)
        self.assertDictEqual(response_body["data"]["registration_details"], {})

        load_user_reward_data(self.airdrop.id, self.loyalty_airdrop_window1.id, LoyaltyAirdropUser1)
        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertTrue(response_body["data"]["is_eligible"])
        self.assertDictEqual(response_body["data"]["registration_details"], {})

        load_airdrop_user_registration(self.loyalty_airdrop_window1.id, LoyaltyAirdropUser1)
        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertTrue(response_body["data"]["is_eligible"])
        assert (len(response_body["data"]["registration_details"]) > 2)

        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertTrue(response_body["data"]["is_already_registered"])

    def test_loyalty_airdrop_user_eligibility_case2(self):
        # User eligible for Window 1 and Not for Window 2
        # User comes directly to Window2, is_eligible flag needs to be true as he has unclaimed rewards from Window 1.
        clear_database()
        self.setUp()
        load_user_reward_data(self.airdrop.id, self.loyalty_airdrop_window1.id, LoyaltyAirdropUser1)
        event = {
            "body": json.dumps({
                "address": LoyaltyAirdropUser1.address,
                "airdrop_id": self.airdrop.id,
                "airdrop_window_id": self.loyalty_airdrop_window2.id
            })
        }
        response = user_eligibility(event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        self.assertTrue(response_body["data"]["is_eligible"])
        self.assertFalse(response_body["data"]["is_claimable"])

    def test_airdrop_window_claim(self):
        load_user_reward_data(self.airdrop.id, self.loyalty_airdrop_window1.id, LoyaltyAirdropUser1)
        load_airdrop_user_registration(self.loyalty_airdrop_window1.id, LoyaltyAirdropUser1)
        event = {
            "body": json.dumps({
                "address": LoyaltyAirdropUser1.address,
                "airdrop_id": str(self.airdrop.id),
                "airdrop_window_id": str(self.loyalty_airdrop_window1.id)
            })
        }
        response = airdrop_window_claim(event=event, context=None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert(response_body["data"]["airdrop_id"]==str(self.airdrop.id))
        assert(response_body["data"]["signature"]=="Not Applicable.")

    def tearDown(self):
        clear_database()
