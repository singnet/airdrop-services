from airdrop.domain.models.airdrop_window import AirdropWindow


class AirdropWindowRuleFactory:
    @staticmethod
    def convert_airdrop_window_rule_model_to_entity_model(window):
        return AirdropWindow(window.airdrop_id, window.id, window.airdrop_window_name,
                             window.description, str(window.registration_start_period), str(window.registration_end_period), window.total_airdrop_tokens).to_dict()
