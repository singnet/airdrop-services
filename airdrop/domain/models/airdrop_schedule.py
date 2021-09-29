class AirdropSchedule:
    def __init__(self, window_id, window_name, info, description, date):
        self._window_id = window_id
        self._window_name = window_name
        self._info = info
        self._description = description
        self._date = date

    def to_dict(self):
        return {
            "airdrop_window_id": self._window_id,
            "airdrop_window_name": self._window_name,
            "airdrop_schedule_info": self._info,
            "airdrop_schedule_description": self._description,
            "airdrop_schedule_date": self._date,
        }
