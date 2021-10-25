from airdrop.domain.models.airdrop_window_timeline import AirdropWindowTimeline


class AirdropWindow:
    def __init__(self, airdrop_id, window_id, window_name,  description, registration_start_period, registration_end_period, total_airdrop_tokens, airdrop_window_timeline, airdrop_window_claim_start_period, airdrop_window_claim_end_period):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._window_name = window_name
        self._description = description
        self._registration_start_period = registration_start_period
        self._registration_end_period = registration_end_period
        self._total_airdrop_tokens = total_airdrop_tokens
        self._airdrop_window_timeline = airdrop_window_timeline
        self._airdrop_window_claim_start_period = airdrop_window_claim_start_period
        self._airdrop_window_claim_end_period = airdrop_window_claim_end_period

    def get_airdrop_window_timeline(self):
        return [
            AirdropWindowTimeline(
                timeline.title, timeline.description, str(timeline.date)).to_dict()
            for timeline in self._airdrop_window_timeline
        ]

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._window_id,
            "airdrop_window_name": self._window_name,
            "airdrop_window_schedule_description": self._description,
            "airdrop_window_registration_start_period": self._registration_start_period,
            "airdrop_window_registration_end_period": self._registration_end_period,
            "airdrop_window_total_tokens": self._total_airdrop_tokens,
            "airdrop_window_claim_start_period": self._airdrop_window_claim_start_period,
            "airdrop_window_claim_end_period": self._airdrop_window_claim_end_period,
            "airdrop_window_timeline": self.get_airdrop_window_timeline()
        }
