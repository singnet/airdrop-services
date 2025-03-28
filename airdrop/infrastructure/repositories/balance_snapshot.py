from typing import List
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.models import UserBalanceSnapshot, AirdropWindow
from airdrop.infrastructure.repositories.base_repository import BaseRepository
from common.logger import get_logger

logger = get_logger(__name__)


class UserBalanceSnapshotRepository(BaseRepository):
    def get_data_by_address(
        self,
        address: str,
        airdrop_id: int
    ) -> List[UserBalanceSnapshot] | None:
        try:
            user_balances = (
                self.session.query(UserBalanceSnapshot)
                .join(
                    AirdropWindow,
                    UserBalanceSnapshot.airdrop_window_id == AirdropWindow.id
                )
                .filter(
                    AirdropWindow.airdrop_id == airdrop_id,
                    UserBalanceSnapshot.address == address
                )
                .all()
            )
            return user_balances
        except SQLAlchemyError as e:
            logger.exception(f"SQLAlchemyError: {e}")
            self.session.rollback()
            raise e

    def get_balances_by_staking_payment_parts_for_airdrop(
        self,
        airdrop_id: int,
        payment_part: str,
        staking_part: str,
    ) -> List[UserBalanceSnapshot] | None:
        try:
            balances = (
                self.session.query(UserBalanceSnapshot)
                .join(
                    AirdropWindow,
                    UserBalanceSnapshot.airdrop_window_id == AirdropWindow.id
                )
                .filter(
                    AirdropWindow.airdrop_id == airdrop_id,
                    or_(
                        UserBalanceSnapshot.payment_part == payment_part,
                        UserBalanceSnapshot.staking_part == staking_part
                    )
                )
            ).all()

            return balances
        except SQLAlchemyError as e:
            logger.exception(f"SQLAlchemyError: {e}")
            self.session.rollback()
            raise e

