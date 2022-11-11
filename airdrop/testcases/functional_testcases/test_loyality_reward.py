import json
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch

from airdrop.infrastructure.models import UserReward
from airdrop.infrastructure.repositories.user_reward_repository import UserRewardRepository
from airdrop.job.eligibility import process_loyalty_airdrop_reward_eligibility
from airdrop.testcases.functional_testcases.load_test_data import clear_database, load_airdrop_data, \
    load_airdrop_window_data
from airdrop.testcases.functional_testcases.loyalty_airdrop_test_data import LoyaltyAirdropData, \
    LoyaltyAirdropWindow1Data, LoyaltyAirdropWindow2Data, LoyaltyAirdropWindow3Data

user_reward_repository = UserRewardRepository()


class TestLoyaltyAirdropServices(TestCase):

    def setUp(self):
        clear_database()
        self.airdrop = load_airdrop_data(LoyaltyAirdropData)
        self.loyalty_airdrop_window1 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow1Data)
        self.loyalty_airdrop_window2 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow2Data)
        self.loyalty_airdrop_window3 = load_airdrop_window_data(self.airdrop.id, LoyaltyAirdropWindow3Data)

    @patch("airdrop.job.reward_processors.loyalty_reward_processor.LoyaltyEligibilityProcessor.get_eligible_users")
    def test_process_loyalty_airdrop_reward_eligibility(self, mock_get_eligible_users):
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
        event = {"airdrop_id": self.airdrop.id, "window_id": self.loyalty_airdrop_window3.id}

        mock_get_eligible_users.return_value = []
        response = process_loyalty_airdrop_reward_eligibility(event, None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert (response_body["message"], "0 users are eligible for claim ")

        mock_get_eligible_users.return_value = [
            {'staker_address': '0x00Aee4E1698Fe0829F4663CBef571c948160B858', 'wallet_address': None,
             'staker_balance': 3016982005590, 'wallet_balance': None, 'is_contract': None}]
        response = process_loyalty_airdrop_reward_eligibility(event, None)
        assert (response["statusCode"] == 200)
        response_body = json.loads(response["body"])
        assert (response_body["message"], "1 users are eligible for claim ")

        user_reward = user_reward_repository.session.query(UserReward).filter(UserReward.airdrop_id == self.airdrop.id,
                                                                              UserReward.airdrop_window_id == self.loyalty_airdrop_window3.id,
                                                                              UserReward.address == "0x00Aee4E1698Fe0829F4663CBef571c948160B858").first()
        assert (user_reward.rewards_awarded, Decimal(22926589306))

    def tearDown(self):
        clear_database()
