from airdrop.infrastructure.repositories.base_repository import BaseRepository
from airdrop.infrastructure.models import AirdropWindow
from sqlalchemy import and_


class AirdropWIndowRepository(BaseRepository):
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
