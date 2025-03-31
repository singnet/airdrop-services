from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.models import PendingTransaction
from airdrop.infrastructure.repositories.base_repository import BaseRepository


class UserPendingRegistrationRepository(BaseRepository):

    def register_user(self, airdrop_window_id: int,
                      address: str, receipt: str,
                      tx_hash: str, signature_details: dict,
                      block_number: int, transaction_type: str) -> None:
        pending_user = PendingTransaction(
            airdrop_window_id=airdrop_window_id,
            address=address,
            receipt_generated=receipt,
            tx_hash=tx_hash,
            signature_details=signature_details,
            user_signature_block_number=block_number,
            transaction_type=transaction_type
        )
        self.add(pending_user)

    def get_all_pending_registrations(self) -> list[PendingTransaction]:
        return self.session.query(PendingTransaction).all()

    def is_pending_user_registration_exist(self, address: str, airdrop_window_id: int) -> bool:
        pending_registrations = (
            self.session.query(PendingTransaction)
            .filter(PendingTransaction.address == address)
            .filter(PendingTransaction.airdrop_window_id == airdrop_window_id)
            .all()
        )
        return True if len(pending_registrations) else False

    def delete_pending_registrations(self, registrations):
        try:
            for registration in registrations:
                self.session.delete(registration)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
