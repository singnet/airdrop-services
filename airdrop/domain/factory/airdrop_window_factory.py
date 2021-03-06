from airdrop.domain.models.airdrop_window import AirdropWindow


class AirdropWindowFactory:
    @staticmethod
    def convert_airdrop_window_model_to_entity_model(window):
        return AirdropWindow(window.airdrop_id, window.id, window.airdrop_window_name,
                             window.description, str(window.registration_start_period), str(window.registration_end_period), window.total_airdrop_tokens, window.timelines, str(window.claim_start_period), str(window.claim_end_period), window.airdropwindow_rules, window.airdrop_window_order).to_dict()
