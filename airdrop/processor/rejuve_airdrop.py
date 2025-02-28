import json
from web3 import Web3

from airdrop.infrastructure.repositories.balance_snapshot import UserBalanceSnapshotRepository
from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.utils import Utils
from common.logger import get_logger
from common.utils import (get_registration_receipt_cardano,
                          get_registration_receipt_ethereum)

logger = get_logger(__name__)


class RejuveAirdrop(DefaultAirdrop):

    def __init__(self, airdrop_id, airdrop_window_id=None):
        super().__init__(airdrop_id, airdrop_window_id)
        self.domain_name = "Rejuve Airdrop"
        self.register_all_window_at_once = False
        self.allow_update_registration = False
        self.is_claim_signature_required = True

    def check_user_eligibility(self, address: str) -> bool:
        user_balance_snapshot_repository = UserBalanceSnapshotRepository()
        user_balance = user_balance_snapshot_repository.get_data_by_address(
            address=address,
            window_id=self.window_id
        )
        if user_balance:
            return True
        return False

    def format_user_registration_signature_message(self, address: str, signature_parameters: dict) -> dict:
        block_number = signature_parameters["block_number"]
        wallet_name = signature_parameters["wallet_name"]
        formatted_message = {
            "airdropId": self.id,
            "airdropWindowId": self.window_id,
            "blockNumber": block_number,
            "walletAddress": address.lower(),
            "walletName": wallet_name
        }
        return json.dumps(formatted_message, separators=(',', ':'))

    def format_and_get_claim_signature_details(self, **kwargs) -> tuple[list, list]:
        pass

    def match_signature(self, data: dict) -> dict:
        address = data["address"].lower()
        signature = data["signature"]
        utils = Utils()
        network = self.recognize_blockchain_network(address)
        logger.info(f"Start of the signature matching for {address = }, {signature = }, {network = }")
        if network == "Ethereum":
            checksum_address = Web3.to_checksum_address(address)
            formatted_message = self.format_user_registration_signature_message(checksum_address, data)
            sign_verified, _ = utils.match_ethereum_signature_eip191(address, formatted_message, signature)
        elif network == "Cardano":
            key = data["key"]
            formatted_message = self.format_user_registration_signature_message(address, data)
            sign_verified, _ = utils.match_cardano_signature(address, formatted_message, signature, key)
        if not sign_verified:
            logger.error("Signature is not valid")
            raise Exception("Signature is not valid.")
        logger.info("Signature validity confirmed")
        return formatted_message

    def recognize_blockchain_network(self, address: str) -> str:
        if address[:2] == "0x":
            return "Ethereum"
        elif address[:4] == "addr":
            return "Cardano"
        else:
            return "Unknown"

    def generate_user_registration_receipt(self, airdrop_id: int,
                                           window_id: int, address: str) -> str:
        # Get the unique receipt to be issued , users can use this receipt as evidence that
        # registration was done
        logger.info("Generate user registration receipt")
        secret_key = self.get_secret_key_for_receipt()
        network = self.recognize_blockchain_network(address)
        if network == "Ethereum":
            receipt = get_registration_receipt_ethereum(airdrop_id, window_id, address, secret_key)
        elif network == "Cardano":
            receipt = get_registration_receipt_cardano(airdrop_id, window_id, address, secret_key)
        return receipt
