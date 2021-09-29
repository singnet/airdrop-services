from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.repositories.base_repository import BaseRepository
from airdrop.infrastructure.models import AirdropWindowTimelines, AirdropWindow
from airdrop.domain.factory.airdrop_factory import AirdropFactory


class AirdropRepository(BaseRepository):
    def get_airdrops_schedule(self, limit, skip):
        try:
            timelines_raw_data = (
                self.session.query(AirdropWindowTimelines)
                .join(
                    AirdropWindow,
                    AirdropWindow.id == AirdropWindowTimelines.airdrop_window_id,
                )
                .limit(limit)
                .offset(skip)
                .order_by(AirdropWindowTimelines.id.desc())
                .all()
            )
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        airdrop_timelines = []
        if timelines_raw_data is not None:
            airdrop_timelines = [
                AirdropFactory.convert_airdrop_schedule_model_to_entity_model(timeline)
                for timeline in timelines_raw_data
            ]
        return airdrop_timelines
