from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.models import UserBalanceSnapshot
from airdrop.infrastructure.repositories.base_repository import BaseRepository


class UserBalanceSnapshotRepository(BaseRepository):

    def get_data_by_address(self, address: str) -> UserBalanceSnapshot | None:
        try:
            user_balance = self.session.query(UserBalanceSnapshot).filter(
                UserBalanceSnapshot.address == address).first()
            return user_balance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
