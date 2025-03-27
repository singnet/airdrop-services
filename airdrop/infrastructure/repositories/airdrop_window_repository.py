from typing import List
from airdrop.infrastructure.repositories.base_repository import BaseRepository
from airdrop.infrastructure.models import AirdropWindow, ClaimHistory
from sqlalchemy import and_


class AirdropWindowRepository(BaseRepository):

    def get_airdrop_window_by_id(self, window_id: int):
        airdrop_window = self.session.query(AirdropWindow).filter(
            AirdropWindow.id == window_id).first()
        return airdrop_window

    def is_airdrop_window_claimed(self, airdrop_window_id, address):
        claim_history = self.session.query(ClaimHistory.id, ClaimHistory.transaction_status) \
            .filter(ClaimHistory.address == address) \
            .filter(ClaimHistory.airdrop_window_id == airdrop_window_id) \
            .first()

        if claim_history is not None:
            return claim_history.transaction_status
        else:
            return None

    def is_open_airdrop_window(self, airdrop_id, airdrop_window_id, date_time):

        return (
            self.session.query(AirdropWindow.id)
            .filter(AirdropWindow.registration_start_period <= date_time)
            .filter(AirdropWindow.registration_end_period >= date_time)
            .filter(
                and_(
                    AirdropWindow.id == airdrop_window_id,
                    AirdropWindow.airdrop_id == airdrop_id,
                )
            )
            .first()
        )

    def get_airdrop_windows(self, airdrop_id: int) -> List[AirdropWindow]:
        return self.session.query(AirdropWindow) \
                   .filter(AirdropWindow.airdrop_id == airdrop_id) \
                   .order_by(AirdropWindow.airdrop_window_order.asc()) \
                   .all()
