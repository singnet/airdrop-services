import inspect

from web3 import Web3

from airdrop.config import NUNET_SIGNER_PRIVATE_KEY
from airdrop.constants import USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT
from airdrop.processor.default_airdrop import DefaultAirdrop
from common.exceptions import RequiredDataNotFound


class NunetAirdrop(DefaultAirdrop):

    def __init__(self, airdrop_id, airdrop_window_id=None):
        super().__init__(airdrop_id, airdrop_window_id)
        self.domain_name = "Nunet Airdrop"
        self.is_claim_signature_required = True
        self.claim_signature_data_format = ["string", "uint256", "uint256", "address",
                                            "uint256", "uint256", "address", "address"]
        self.claim_signature_private_key_secret = NUNET_SIGNER_PRIVATE_KEY
        self.reward_processor_name = "nunet_reward_processor.NunetRewardProcessor"

    def format_user_registration_signature_message(self, address: str, signature_parameters: dict):
        block_number = signature_parameters["block_number"]
        formatted_message = USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT
        formatted_message["message"] = {
            "Airdrop": {
                "airdropId": self.id,
                "airdropWindowId": self.window_id,
                "blockNumber": block_number,
                "walletAddress": address
            },
        }
        formatted_message["domain"]["name"] = self.domain_name
        return formatted_message

    def format_and_get_claim_signature_details(self, **kwargs):
        signature_parameters = kwargs.get("signature_parameters")
        if not signature_parameters:
            raise RequiredDataNotFound("signature_parameters parameter "
                                       "not passed to function "
                                       f"{inspect.currentframe().f_code.co_name} "
                                       f"for airdrop_id = {self.id}, " 
                                       f"window_id = {self.window_id}")

        total_eligible_amount = signature_parameters["total_eligible_amount"]
        contract_address = Web3.to_checksum_address(signature_parameters["contract_address"])
        token_address = Web3.to_checksum_address(signature_parameters["token_address"])
        user_address = Web3.to_checksum_address(signature_parameters["user_address"])
        amount = signature_parameters["claimable_amount"]
        formatted_message = ["__airdropclaim", total_eligible_amount, amount, user_address, int(self.id),
                             int(self.window_id), contract_address, token_address]
        return self.claim_signature_data_format, formatted_message
