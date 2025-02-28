from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.models import UserBalanceSnapshot
from airdrop.infrastructure.repositories.base_repository import BaseRepository
from common.logger import get_logger

logger = get_logger(__name__)


class UserBalanceSnapshotRepository(BaseRepository):

    def get_data_by_address(self, address: str, window_id: int) -> UserBalanceSnapshot | None:
        try:
            user_balance = self.session.query(UserBalanceSnapshot).filter(
                UserBalanceSnapshot.address == address).filter(
                UserBalanceSnapshot.airdrop_window_id == window_id).first()
            return user_balance
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError: {e}")
            self.session.rollback()
            raise e
