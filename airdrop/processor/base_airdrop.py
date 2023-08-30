

class BaseAirdrop:

    def __init__(self, airdrop_id, airdrop_window_id=None):
        self.domain_name = "Base Airdrop"
        self.airdrop_id = airdrop_id
        self.airdrop_window_id = airdrop_window_id
        self.register_all_window_at_once = False
        self.allow_update_registration = False
        self.is_claim_signature_required = False
        self.chain_context = {}
        self.reward_processor_name = ""

    @staticmethod
    def check_user_eligibility(user_eligible_for_given_window, unclaimed_reward):
        return user_eligible_for_given_window

    def format_user_registration_signature_message(self, address, signature_parameters):
        pass

    def format_and_get_claim_signature_details(self, signature_parameters):
        pass
