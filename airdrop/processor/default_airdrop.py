from airdrop.constants import USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT
from airdrop.processor.base_airdrop import BaseAirdrop


class DefaultAirdrop(BaseAirdrop):
    def __init__(self, airdrop_id, airdrop_window_id=None):
        self.airdrop_id = airdrop_id
        self.airdrop_window_id = airdrop_window_id
        self.register_all_window_at_once = False
        self.domain_name = "Nunet Airdrop"
        self.chain_context = {}

    def format_signature_message(self, address, signature_parameters):
        block_number = signature_parameters["block_number"]
        formatted_message = USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT
        formatted_message["message"] = {
            "Airdrop": {
                "airdropId": self.airdrop_id,
                "airdropWindowId": self.airdrop_window_id,
                "blockNumber": block_number,
                "walletAddress": address
            },
        }
        formatted_message["domain"]["name"] = self.domain_name
        return formatted_message

    @staticmethod
    def check_user_eligibility(user_eligible_for_given_window, unclaimed_reward):
        return user_eligible_for_given_window

    @staticmethod
    def trim_prefix_from_string_message(prefix, message):
        # move to utils
        if message.startswith(prefix):
            message = message[len(prefix):]
        return message
