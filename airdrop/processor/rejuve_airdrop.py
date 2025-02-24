from web3 import Web3

from airdrop.constants import USER_REGISTRATION_SIGNATURE_REJUVE_AIRDROP_FORMAT
from airdrop.infrastructure.repositories.balance_snapshot import UserBalanceSnapshotRepository
from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.utils import Utils


class RejuveAirdrop(DefaultAirdrop):

    def __init__(self, airdrop_id, airdrop_window_id=None):
        super().__init__(airdrop_id, airdrop_window_id)
        self.domain_name = "Rejuve Airdrop"
        self.register_all_window_at_once = False
        self.allow_update_registration = False
        self.is_claim_signature_required = True

    def check_user_eligibility(self, address: str) -> bool:
        user_balance = UserBalanceSnapshotRepository.get_data_by_address(address)
        if user_balance:
            return True
        return False

    def format_user_registration_signature_message(self, address: str, signature_parameters: dict) -> dict:
        block_number = signature_parameters["block_number"]
        wallet_name = signature_parameters["wallet_name"]
        formatted_message = USER_REGISTRATION_SIGNATURE_REJUVE_AIRDROP_FORMAT
        formatted_message["message"] = {
            "Airdrop": {
                "airdropId": self.id,
                "airdropWindowId": self.window_id,
                "blockNumber": block_number,
                "walletAddress": address,
                "walletName": wallet_name
            },
        }
        formatted_message["domain"]["name"] = self.domain_name
        return formatted_message

    def format_and_get_claim_signature_details(self, **kwargs) -> tuple[list, list]:
        pass

    def match_signature(self, data: dict) -> dict:
        address = data["address"].lower()
        checksum_address = Web3.toChecksumAddress(address)
        signature = data["signature"]
        utils = Utils()
        network = self.recognize_blockchain_network(address)
        if network == "Ethereum":
            formatted_message = self.format_user_registration_signature_message(checksum_address, data)
            formatted_signature = utils.trim_prefix_from_string_message(prefix="0x", message=signature)
            sign_verified, _ = utils.match_ethereum_signature(address, formatted_message, formatted_signature)
        elif network == "Cardano":
            key = data["key"]
            formatted_message = self.format_user_registration_signature_message(checksum_address, data)
            sign_verified, _ = utils.match_cardano_signature(address, formatted_message, signature, key)
        if not sign_verified:
            raise Exception("Signature is not valid.")
        return formatted_message

    def recognize_blockchain_network(self, address: str) -> str:
        if address[:2] == "0x":
            return "Ethereum"
        elif address[:4] == "addr":
            return "Cardano"
        else:
            return "Unknown"
