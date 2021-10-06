from airdrop.domain.models.airdrop_schedule import AirdropSchedule
from airdrop.domain.models.airdrop_window import AirdropWindow
from airdrop.domain.models.airdrop_user_details import AirdropUserDetails


class AirdropFactory:
    @staticmethod
    def convert_airdrop_schedule_model_to_entity_model(timeline):
        return AirdropSchedule(
            timeline.airdrop_window_id,
            timeline.airdrop_window.airdrop_window_name,
            timeline.title,
            timeline.description,
            str(timeline.date),
        ).to_dict()

    @staticmethod
    def convert_airdrop_window_model_to_entity_model(window):
        return AirdropWindow(
            window.airdrop_id,
            window.id,
            window.airdrop_window_name,
            window.description,
            str(window.registration_start_period),
            str(window.registration_end_period),
        ).to_dict()

    @staticmethod
    def convert_airdrop_window_user_model_to_entity_model(user):
        return AirdropUserDetails(
            user.airdrop_window.airdrop_id,
            user.airdrop_window.id,
            user.address,
            str(user.registered_at)
        ).to_dict()
