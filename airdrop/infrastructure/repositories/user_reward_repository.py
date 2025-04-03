from decimal import Decimal
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError
from airdrop.constants import CardanoEra, CARDANO_ADDRESS_PREFIXES
from airdrop.infrastructure.repositories.base_repository import BaseRepository
from airdrop.infrastructure.models import UserReward, UserRegistration, UserBalanceSnapshot


class UserRewardRepository(BaseRepository):

    @staticmethod
    def create_user_reward(airdrop_id: int,
                           airdrop_window_id: int,
                           address: str,
                           condition: str | None,
                           rewards_awarded: Decimal,
                           score: Decimal,
                           normalized_score: Decimal):
        user_reward = UserReward(
            airdrop_id=airdrop_id,
            airdrop_window_id=airdrop_window_id,
            address=address,
            condition=condition,
            rewards_awarded=rewards_awarded,
            score=score,
            normalized_score=normalized_score
        )
        return user_reward

    def get_ethereum_registrations_balances(self,
                                            airdrop_window_id: int,
                                            snapshot_window_id: int = None,
                                            snapshot_guid: str = None):
        query = select(UserRegistration.address,
                       UserBalanceSnapshot.balance,
                       UserBalanceSnapshot.staked,
                       UserBalanceSnapshot.total)\
            .join(UserBalanceSnapshot, UserRegistration.address == UserBalanceSnapshot.address)\
            .where(UserRegistration.airdrop_window_id == airdrop_window_id,
                   UserRegistration.address.like("0x%"))
        if snapshot_window_id is not None:
            query = query.where(UserBalanceSnapshot.airdrop_window_id == snapshot_window_id)
        if snapshot_guid is not None:
            query = query.where(UserBalanceSnapshot.snapshot_guid == snapshot_guid)
        result = self.session.execute(query).all()
        return result

    def get_cardano_registrations(self, airdrop_window_id: int, *, address_era: CardanoEra = CardanoEra.ANY):
        prefixes = CARDANO_ADDRESS_PREFIXES[address_era]
        query = select(UserRegistration.address)\
            .where(UserRegistration.airdrop_window_id == airdrop_window_id)\
            .where(or_(UserRegistration.address.like(f"{prefix}%") for prefix in prefixes))
        result = self.session.execute(query).all()
        return result

    def get_cardano_balances(self,
                             address: str | None = None,
                             payment_part: str | None = None,
                             staking_part: str | None = None,
                             *,
                             snapshot_window_id: int | None = None,
                             snapshot_guid: str | None = None):
        if not address and not payment_part and not staking_part:
            raise ValueError("At least one of address / payment_part / staking_part arguments must be provided")
        or_clause = list()
        if address:
            or_clause.append(UserBalanceSnapshot.address == address)
        if payment_part:
            or_clause.append(UserBalanceSnapshot.payment_part == payment_part)
        if staking_part:
            or_clause.append(UserBalanceSnapshot.staking_part == staking_part)
        query = select(UserBalanceSnapshot.address,
                       UserBalanceSnapshot.payment_part,
                       UserBalanceSnapshot.staking_part,
                       UserBalanceSnapshot.balance,
                       UserBalanceSnapshot.staked,
                       UserBalanceSnapshot.total)\
            .where(or_(*or_clause))
        if snapshot_window_id is not None:
            query = query.where(UserBalanceSnapshot.airdrop_window_id == snapshot_window_id)
        if snapshot_guid:
            query = query.where(UserBalanceSnapshot.snapshot_guid == snapshot_guid)
        result = self.session.execute(query).all()
        return result
