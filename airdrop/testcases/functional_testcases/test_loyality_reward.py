import json
from unittest import TestCase

from airdrop.job.eligibility import process_loyalty_airdrop_reward_eligibility
from airdrop.testcases.functional_testcases.load_test_data import clear_database, load_airdrop_data, \
    load_airdrop_window_data
from airdrop.testcases.functional_testcases.loyalty_airdrop_test_data import LoyaltyAirdropData, \
    LoyaltyAirdropWindow1Data, LoyaltyAirdropWindow2Data


class TestLoyaltyAirdropServices(TestCase):

    def setUp(self):
        clear_database()
        self.airdrop = load_airdrop_data(LoyaltyAirdropData)
        self.loyalty_airdrop_window1 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow1Data)
        self.loyalty_airdrop_window2 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow2Data)

    def test_process_loyalty_airdrop_reward_eligibility(self):
        event = dict()

        # Empty input
        response = process_loyalty_airdrop_reward_eligibility(event, None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert (response_body["message"], "failed")

        # Without input values
        event = {"airdrop_id": None, "window_id": None}

        response = process_loyalty_airdrop_reward_eligibility(event, None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert (response_body["message"], "failed")

        # invalid input values
        event = {"airdrop_id": 10, "window_id": 200}

        response = process_loyalty_airdrop_reward_eligibility(event, None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert (response_body["message"], "'Validation failed'")

        # older window id provided because claim has been already started
        event = {"airdrop_id": self.airdrop.id, "window_id": self.loyalty_airdrop_window1.id}

        response = process_loyalty_airdrop_reward_eligibility(event, None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert (response_body["message"], "'Validation failed'")

        # newer window id provided because claim has not been already started
        event = {"airdrop_id": self.airdrop.id, "window_id": self.loyalty_airdrop_window2.id}

        response = process_loyalty_airdrop_reward_eligibility(event, None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert (response_body["message"], "'Validation failed'")

    def tearDown(self):
        clear_database()
updat