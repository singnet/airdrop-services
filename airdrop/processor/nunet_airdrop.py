from web3 import Web3

from airdrop.config import NUNET_SIGNER_PRIVATE_KEY
from airdrop.constants import USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT
from airdrop.processor.base_airdrop import BaseAirdrop


class NunetAirdrop(BaseAirdrop):
    def __init__(self, airdrop_id, airdrop_window_id=None):
        self.airdrop_id = airdrop_id
        self.airdrop_window_id = airdrop_window_id
        self.register_all_window_at_once = False
        self.domain_name = "Nunet Airdrop"
        self.chain_context = {}
        self.is_claim_signature_required = True
        self.claim_signature_data_format = ["string", "uint256", "uint256", "address", "uint256", "uint256", "address",
                                            "address"]
        self.claim_signature_private_key_secret = NUNET_SIGNER_PRIVATE_KEY
        self.reward_processor_name = "nunet_reward_processor.NunetRewardProcessor"

    def format_user_registration_signature_message(self, address, signature_parameters):
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

    def format_and_get_claim_signature_details(self, signature_parameters):
        total_eligible_amount = signature_parameters["total_eligible_amount"]
        contract_address = Web3.toChecksumAddress(signature_parameters["contract_address"])
        token_address = Web3.toChecksumAddress(signature_parameters["token_address"])
        user_address = Web3.toChecksumAddress(signature_parameters["user_address"])
        amount = signature_parameters["claimable_amount"]
        formatted_message = ["__airdropclaim", total_eligible_amount, amount, user_address, int(self.airdrop_id),
                             int(self.airdrop_window_id), contract_address, token_address]
        return self.claim_signature_data_format, formatted_message
