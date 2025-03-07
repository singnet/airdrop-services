from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.constants import (USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT,
                               USER_CLAIM_SIGNATURE_DEFAULT_FORMAT)
from airdrop.config import LoyaltyAirdropConfig


class LoyaltyAirdrop(DefaultAirdrop):

    def __init__(self, airdrop_id, airdrop_window_id=None):
        super().__init__(airdrop_id, airdrop_window_id)
        self.domain_name = "SingularityNet"
        self.register_all_window_at_once = True
        self.allow_update_registration = True
        self.is_claim_signature_required = False
        self.chain_context = {
            "deposit_address": LoyaltyAirdropConfig.deposit_address.value,
            "amount": LoyaltyAirdropConfig.pre_claim_transfer_amount.value["amount"],
            "chain": LoyaltyAirdropConfig.chain.value
        }
        self.claim_address = LoyaltyAirdropConfig.claim_address.value

    def check_user_eligibility(self, address: str) -> bool:
        if not isinstance(address, str):
            raise Exception("The address was sent in the wrong format.")

        address = address.lower()
        registration_repo = UserRegistrationRepository()
        user_eligible_for_given_window = registration_repo.is_user_eligible_for_given_window(
            address, self.id, self.window_id
        )
        unclaimed_reward = registration_repo.get_unclaimed_reward(self.id, address)

        if user_eligible_for_given_window or unclaimed_reward > 0:
            return True
        return False

    def format_user_registration_signature_message(self, address: str, signature_parameters: dict) -> dict:
        block_number = signature_parameters["block_number"]
        cardano_address = signature_parameters["cardano_address"]
        cardano_wallet_name = signature_parameters["cardano_wallet_name"]
        formatted_message = USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT
        formatted_message["message"] = {
            "Airdrop": {
                "airdropId": self.id,
                "airdropWindowId": self.window_id,
                "blockNumber": block_number,
                "walletAddress": address,
                "cardanoAddress": cardano_address,
                "cardanoWalletName": cardano_wallet_name
            },
        }
        formatted_message["domain"]["name"] = self.domain_name
        return formatted_message

    def format_and_get_claim_signature_details(self, **kwargs) -> None:
        pass

    def format_user_claim_signature_message(self, receipt: str) -> dict:
        formatted_message = USER_CLAIM_SIGNATURE_DEFAULT_FORMAT
        formatted_message["message"] = {
            "Airdrop": {
                "airdropWindowId": int(self.window_id),
                "receipt": receipt
            },
        }
        formatted_message["domain"]["name"] = self.domain_name
        return formatted_message
