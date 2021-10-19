class AirdropWindowTimeline:
    def __init__(self, title, description, date):
        self._title = title
        self._description = description
        self._date = date

    def to_dict(self):
        return {
            "airdrop_window_timeline_title":  self._title,
            "airdrop_window_timeline_description": self._description,
            "airdrop_window_timeline_date": self._date
        }
