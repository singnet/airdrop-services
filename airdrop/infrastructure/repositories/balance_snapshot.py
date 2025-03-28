from typing import List
from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.models import UserBalanceSnapshot, AirdropWindow
from airdrop.infrastructure.repositories.base_repository import BaseRepository
from common.logger import get_logger

logger = get_logger(__name__)


class UserBalanceSnapshotRepository(BaseRepository):
    def get_data_by_address(
        self, address: str, window_id: int
    ) -> UserBalanceSnapshot | None:
        try:
            user_balance = (
                self.session.query(UserBalanceSnapshot)
                .filter(
                    UserBalanceSnapshot.address == address,
                    UserBalanceSnapshot.airdrop_window_id == window_id,
                )
                .first()
            )
            return user_balance
        except SQLAlchemyError as e:
            logger.exception(f"SQLAlchemyError: {e}")
            self.session.rollback()
            raise e

    def get_balances_by_address_for_airdrop(
        self,
        airdrop_id: int,
        payment_part: str | None = None,
        staking_part: str | None = None,
    ) -> List[UserBalanceSnapshot] | None:
        try:
            query = (
                self.session.query(UserBalanceSnapshot)
                .join(
                    AirdropWindow,
                    UserBalanceSnapshot.airdrop_window_id == AirdropWindow.id
                )
                .filter(
                    AirdropWindow.airdrop_id == airdrop_id,
                )
            )

            if payment_part:
                query = query.filter(UserBalanceSnapshot.payment_part == payment_part)
            
            if staking_part:
                query = query.filter(UserBalanceSnapshot.staking_part == staking_part)

            return query.all()
        except SQLAlchemyError as e:
            logger.exception(f"SQLAlchemyError: {e}")
            self.session.rollback()
            raise e
