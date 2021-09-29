from airdrop.domain.models.airdrop_schedule import AirdropSchedule


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
