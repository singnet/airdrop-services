from web3 import Web3

from airdrop.constants import USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT


class DefaultAirdrop:
    def __int__(self, airdrop_id, airdrop_window_id=None):
        self.airdrop_id = airdrop_id
        self.airdrop_window_id = airdrop_window_id
        self.register_all_window_at_once = False

    def format_signature_message(self, address, signature_parameters):
        block_number = signature_parameters["block_number"]
        message = {
            "Airdrop": {
                "airdropId": self.airdrop_id,
                "airdropWindowId": self.airdrop_window_id,
                "blockNumber": block_number,
                "walletAddress": address
            },
        }
        formatted_message = USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT
        formatted_message["message"] = message
        return formatted_message

    @staticmethod
    def trim_prefix_from_string_message(prefix, message):
        # move to utils
        if message.startswith(prefix):
            message = message[len(prefix):]
        return message
