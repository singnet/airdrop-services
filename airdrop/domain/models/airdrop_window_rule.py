class AirdropWindowRule:
    def __init__(self, title, rule):
        self._title = title
        self._rule = rule

    def to_dict(self):
        return {
            "airdrop_window_eligibility_title":  self._title,
            "airdrop_window_eligibility_rule": self._rule,
        }
