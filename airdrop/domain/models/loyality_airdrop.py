from airdrop.constants import USER_REGISTRATION_SIGNATURE_LOYALITY_AIRDROP_FORMAT
from airdrop.domain.models.base_airdrop import BaseAirdrop


class LoyalityAirdrop(BaseAirdrop):
    def __init__(self, airdrop_id, airdrop_window_id=None):
        self.airdrop_id = airdrop_id
        self.airdrop_window_id = airdrop_window_id
        self.register_all_window_at_once = True

    def format_signature_message(self, address, signature_parameters):
        block_number = signature_parameters["block_number"]
        cardano_address = signature_parameters["cardano_address"]
        message = {
            "Airdrop": {
                "airdropId": self.airdrop_id,
                "airdropWindowId": self.airdrop_window_id,
                "blockNumber": block_number,
                "walletAddress": address,
                "cardanoAddress": cardano_address
            },
        }
        formatted_message = USER_REGISTRATION_SIGNATURE_LOYALITY_AIRDROP_FORMAT
        formatted_message["message"] = message
        return formatted_message

    @staticmethod
    def trim_prefix_from_string_message(prefix, message):
        # move to utils
        if message.startswith(prefix):
            message = message[len(prefix):]
        return message
