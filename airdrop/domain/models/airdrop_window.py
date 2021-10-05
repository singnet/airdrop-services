class AirdropWindow:
    def __init__(self, airdrop_id, window_id, window_name,  description, registration_start_period, registration_end_period):
        print('Called')
        print(airdrop_id)
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._window_name = window_name
        self._description = description
        self._registration_start_period = registration_start_period
        self._registration_end_period = registration_end_period

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._window_id,
            "airdrop_window_name": self._window_name,
            "airdrop_schedule_description": self._description,
            "airdrop_registration_start_period": self._registration_start_period,
            "airdrop_registration_end_period": self._registration_end_period,
        }
