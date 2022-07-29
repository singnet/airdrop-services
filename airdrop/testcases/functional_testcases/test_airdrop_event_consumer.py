import json
from unittest import TestCase

from py_eth_sig_utils.signing import v_r_s_to_signature, sign_typed_data

from airdrop.application.handlers.consumer_handler import deposit_event_consumer
from airdrop.constants import USER_CLAIM_SIGNATURE_DEFAULT_FORMAT
from airdrop.testcases.functional_testcases.event_consumer_test_data import DEPOSIT_EVENT
from airdrop.testcases.functional_testcases.load_test_data import load_airdrop_user_registration, load_user_reward_data, \
    clear_database, load_airdrop_data, load_airdrop_window_data
from airdrop.testcases.functional_testcases.loyalty_airdrop_test_data import LoyaltyAirdropUser1, LoyaltyAirdropData, \
    LoyaltyAirdropWindow1Data, LoyaltyAirdropWindow2Data


class TestAirdropEventConsumer(TestCase):
    def setUp(self):
        clear_database()
        self.airdrop = load_airdrop_data(LoyaltyAirdropData)
        self.loyalty_airdrop_window1 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow1Data)
        self.loyalty_airdrop_window2 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow2Data)

    def test_deposit_event_consumer(self):
        load_user_reward_data(self.airdrop.id, self.loyalty_airdrop_window1.id, LoyaltyAirdropUser1)
        load_airdrop_user_registration(self.loyalty_airdrop_window1.id, LoyaltyAirdropUser1, "Loyalty Airdrop")
        formatted_message = USER_CLAIM_SIGNATURE_DEFAULT_FORMAT
        formatted_message["message"] = {
            "Airdrop": {
                "airdropWindowId": self.loyalty_airdrop_window1.id,
                "receipt": LoyaltyAirdropUser1.receipt_generated
            }
        }
        formatted_message["domain"]["name"] = LoyaltyAirdropUser1.signature_details["domain_name"]
        signature = v_r_s_to_signature(*sign_typed_data(formatted_message, LoyaltyAirdropUser1.private_key)).hex()
        event = DEPOSIT_EVENT
        deposit_event_body = json.loads(event["Records"][0]["body"])
        deposit_event_message = json.loads(deposit_event_body["Message"])
        deposit_event_message["transaction_detail"]["tx_metadata"][0]["json_metadata"] = {
            "r1": LoyaltyAirdropUser1.receipt_generated[0:64],
            "r2": LoyaltyAirdropUser1.receipt_generated[64:88],
            "wid": str(self.loyalty_airdrop_window1.id),
            "s1": signature[0:64],
            "s2": signature[64:128],
            "s3": signature[128:130],
        }
        deposit_event_body.update({"Message": json.dumps(deposit_event_message)})
        event["Records"][0].update({"body": json.dumps(deposit_event_body)})
        # response = deposit_event_consumer(event, context=None)
        # print(response)

    def tearDown(self):
        clear_database()
