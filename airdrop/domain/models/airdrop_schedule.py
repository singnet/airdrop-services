from airdrop.domain.factory.airdrop_window_factory import AirdropWindowFactory


class AirdropSchedule:
    def __init__(self, airdrop_id, token_name, airdrop_description, airdrop_portal_link, airdrop_documentation_link, airdrop_github_link, rules, airdrop_windows):
        self._airdrop_id = airdrop_id
        self._token_name = token_name
        self._airdrop_description = airdrop_description
        self._airdrop_portal_link = airdrop_portal_link
        self._airdrop_documentation_link = airdrop_documentation_link
        self._airdrop_github_link = airdrop_github_link
        self._rules = rules
        self._airdrop_windows = airdrop_windows

    def get_airdrop_windows(self):
        return [
            AirdropWindowFactory.convert_airdrop_window_model_to_entity_model(
                window)
            for window in self._airdrop_windows
        ]

    def to_dict(self):

        airdrop_windows = self.get_airdrop_windows()
        airdrop_total_tokens = 0

        for window in airdrop_windows:
            airdrop_total_tokens += window['airdrop_window_total_tokens']

        return {
            "airdrop_id": self._airdrop_id,
            "token_name": self._token_name,
            "airdrop_description": self._airdrop_description,
            "airdrop_portal_link": self._airdrop_portal_link,
            "airdrop_documentation_link": self._airdrop_documentation_link,
            "airdrop_github_link_for_contract": self._airdrop_github_link,
            "airdrop_rules": self._rules,
            "airdrop_total_tokens": airdrop_total_tokens,
            "airdrop_windows": airdrop_windows
        }
