from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.repositories.base_repository import BaseRepository
from airdrop.infrastructure.models import AirdropWindowTimelines, AirdropWindow, Airdrop
from airdrop.domain.factory.airdrop_factory import AirdropFactory


class AirdropRepository(BaseRepository):

    def register_airdrop(self, address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link_for_contract):
        airdrop = Airdrop(
            address=address, org_name=org_name, token_name=token_name, contract_address=contract_address, portal_link=portal_link, documentation_link=documentation_link, description=description, github_link_for_contract=github_link_for_contract, token_type=token_type)
        return self.session.add(airdrop)

    def register_airdrop_window(self, airdrop_id, airdrop_window_name, description, registration_required, registration_start_period, registration_end_period, snapshot_required, claim_start_period, claim_end_period):
        airdrop_window = AirdropWindow(airdrop_id=airdrop_id, airdrop_window_name=airdrop_window_name, description=description, registration_required=registration_required, registration_start_period=registration_start_period,
                                       registration_end_period=registration_end_period, snapshot_required=snapshot_required, claim_start_period=claim_start_period, claim_end_period=claim_end_period)
        return self.session.add(airdrop_window)

    def get_airdrops(self, limit, skip):
        try:

            airdrop_window_data = (
                self.session.query(AirdropWindow)
                .limit(limit)
                .offset(skip)
                .all()
            )
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        airdrop_windows = []
        if airdrop_window_data is not None:
            airdrop_windows = [
                AirdropFactory.convert_airdrop_window_model_to_entity_model(
                    window)
                for window in airdrop_window_data
            ]
        return airdrop_windows

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
                .all()
            )
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        airdrop_timelines = []
        if timelines_raw_data is not None:
            airdrop_timelines = [
                AirdropFactory.convert_airdrop_schedule_model_to_entity_model(
                    timeline)
                for timeline in timelines_raw_data
            ]
        return airdrop_timelines
