import pycardano
from decimal import Decimal, ROUND_DOWN
from airdrop.constants import CardanoEra
from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.processor.rejuve_airdrop import RejuveAirdrop
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_reward_repository import UserRewardRepository
from common.logger import get_logger

logger = get_logger(__name__)


class RejuveRewardProcessor:

    REWARD_STAKE_RATIO = Decimal("0.2")
    REWARD_SCORE_DENOM = Decimal("100_000")
    TOKEN_DECIMALS = 6

    def __init__(self, airdrop_id: int, airdrop_window_id: int, snapshot_guid: str):
        logger.info(f"Init Rejuve Rewards Processor for airdrop_id={airdrop_id}, "
                    f"airdrop_window_id={airdrop_window_id}, snapshot_guid={snapshot_guid}")

        self.airdrop_id = airdrop_id
        self.airdrop_window_id = airdrop_window_id
        self.snapshot_guid = snapshot_guid

        self.airdrop_repository = AirdropRepository()
        self.airdrop_window_repository = AirdropWindowRepository()
        self.user_reward_repository = UserRewardRepository()

        try:

            airdrop_details = self.airdrop_repository.get_airdrop_details(self.airdrop_id)
            assert airdrop_details is not None, "Airdrop id is not valid"
            self.airdrop = airdrop_details

            airdrop_class = AirdropServices.load_airdrop_class(airdrop_details)
            assert airdrop_class is RejuveAirdrop, "Airdrop class is not RejuveAirdrop"
            self.airdrop_object = airdrop_class(self.airdrop_id)

            airdrop_window_details = self.airdrop_repository.get_airdrop_window_details(self.airdrop_window_id)
            assert airdrop_window_details, "Airdrop window id is not valid"
            assert airdrop_window_details.airdrop_id == self.airdrop_id, "Airdrop window id doesn't match airdrop id"
            self.airdrop_window = airdrop_window_details

            airdrop_windows = self.airdrop_window_repository.get_airdrop_windows(self.airdrop_id)
            assert airdrop_windows, f"No windows for airdrop_id={self.airdrop_id}"
            self.airdrop_windows = airdrop_windows
            self.airdrop_first_window_id = airdrop_windows[0].id

            self.total_window_rewards = self.airdrop_window.total_airdrop_tokens * 10**self.TOKEN_DECIMALS

            logger.info(f"Found Airdrop \"{self.airdrop.org_name}\" with {len(airdrop_windows)} windows, first window "
                        f"id = {self.airdrop_first_window_id}, total window rewards = {self.total_window_rewards}")

        except AssertionError as e:
            logger.error(e)
            raise e

    def process_user_rewards(self):
        logger.info(f"Processing Rejuve Rewards for airdrop_id={self.airdrop_id} "
                    f"and airdrop_window_id={self.airdrop_window_id}")

        address_score = {}
        total_score = Decimal(0)

        ethereum_addresses = self.user_reward_repository.get_ethereum_registrations_balances(
            airdrop_window_id=self.airdrop_window_id,
            snapshot_window_id=self.airdrop_first_window_id,
            snapshot_guid=self.snapshot_guid)
        amount = len(ethereum_addresses)
        for index, row in enumerate(ethereum_addresses):
            score, normalized_score = self.calculate_score(row.balance, row.staked)
            address_score[row.address] = (score, normalized_score)
            total_score += normalized_score
            logger.info(f"[{index+1}/{amount}] Ethereum address {row.address} with balance={row.balance} and "
                        f"stake={row.staked}, calculated normalized score = {normalized_score}")

        cardano_byron_addresses = self.user_reward_repository.get_cardano_registrations(
            airdrop_window_id=self.airdrop_window_id,
            address_era=CardanoEra.BYRON
        )
        amount = len(cardano_byron_addresses)
        for index, row in enumerate(cardano_byron_addresses):
            total_balance = Decimal(0)
            total_stake = Decimal(0)
            snapshot_balances = self.user_reward_repository.get_cardano_balances(
                address=row.address,
                snapshot_window_id=self.airdrop_first_window_id,
                snapshot_guid=self.snapshot_guid)
            for balance in snapshot_balances:
                total_balance += balance.balance
                total_stake += balance.staked
            score, normalized_score = self.calculate_score(total_balance, total_stake)
            address_score[row.address] = (score, normalized_score)
            total_score += normalized_score
            logger.info(f"[{index+1}/{amount}] Cardano Byron address {row.address} and {len(snapshot_balances)} "
                        f"related addresses with total balance={total_balance} and stake={total_stake}, "
                        f"calculated normalized score = {normalized_score}")

        cardano_shelley_addresses = self.user_reward_repository.get_cardano_registrations(
            airdrop_window_id=self.airdrop_window_id,
            address_era=CardanoEra.SHELLEY
        )
        amount = len(cardano_shelley_addresses)
        for index, row in enumerate(cardano_shelley_addresses):
            total_balance = Decimal(0)
            total_stake = Decimal(0)
            address_obj = pycardano.Address.decode(row.address)
            payment_part = str(address_obj.payment_part) if address_obj.payment_part else None
            staking_part = str(address_obj.staking_part) if address_obj.staking_part else None
            snapshot_balances = self.user_reward_repository.get_cardano_balances(
                address=row.address,
                payment_part=payment_part,
                staking_part=staking_part,
                snapshot_window_id=self.airdrop_first_window_id,
                snapshot_guid=self.snapshot_guid)
            for balance in snapshot_balances:
                total_balance += balance.balance
                total_stake += balance.staked
            score, normalized_score = self.calculate_score(total_balance, total_stake)
            address_score[row.address] = (score, normalized_score)
            total_score += normalized_score
            logger.info(f"[{index + 1}/{amount}] Cardano Shelley address {row.address} and {len(snapshot_balances)} "
                        f"related addresses with total balance={total_balance} and stake={total_stake}, "
                        f"calculated normalized score = {normalized_score}")

        user_rewards = []
        for key, value in address_score.items():
            address = key
            score, normalized_score = value
            reward = self.calculate_reward(normalized_score, total_score)
            user_reward = self.user_reward_repository.create_user_reward(
                airdrop_id=self.airdrop_id,
                airdrop_window_id=self.airdrop_window_id,
                address=address,
                condition=None,
                rewards_awarded=reward,
                score=score,
                normalized_score=normalized_score
            )
            user_rewards.append(user_reward)
        self.user_reward_repository.add_all_items(user_rewards)  # TODO: batching

    def calculate_score(self, balance: Decimal, stake: Decimal) -> (Decimal, Decimal):
        score = (balance + self.REWARD_STAKE_RATIO * stake) / self.REWARD_SCORE_DENOM
        normalized_score = (score + 1).log10()
        return score, normalized_score

    def calculate_reward(self, score: Decimal, total_score: Decimal) -> Decimal:
        reward = score / total_score * self.total_window_rewards
        reward = reward.quantize(Decimal("1."), rounding=ROUND_DOWN)
        return reward
