import json
from typing import Dict, List, Union
from web3 import Web3

from airdrop.constants import AirdropClaimStatus
from airdrop.infrastructure.models import UserRegistration
from airdrop.application.types.windows import WindowRegistrationData
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

    def format_user_registration_signature_message(
        self,
        address: str,
        signature_parameters: dict
    ) -> dict:
        block_number = signature_parameters["block_number"]
        wallet_name = signature_parameters["wallet_name"]
        formatted_message = {
            "airdropId": self.id,
            "airdropWindowId": self.window_id,
            "blockNumber": block_number,
            "walletAddress": address.lower(),
            "walletName": wallet_name
        }
        return formatted_message

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
            message = json.dumps(formatted_message, separators=(',', ':'))
            sign_verified = utils.match_ethereum_signature_eip191(address, message, signature)
        elif network == "Cardano":
            key = data["key"]
            formatted_message = self.format_user_registration_signature_message(address, data)
            message = json.dumps(formatted_message, separators=(',', ':'))
            sign_verified = utils.match_cardano_signature(message, signature, key)
        if not sign_verified:
            logger.error("Signature is not valid")
            raise Exception("Signature is not valid.")
        logger.info("Signature validity confirmed")
        return message

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

    def generate_multiple_windows_eligibility_response(
        self,
        is_user_eligible: bool,
        airdrop_id: int,
        address: str,
        windows_registration_data: List[WindowRegistrationData],
        rewards_awarded: int,
        with_signature: bool,
    ):
        response = {
            "is_eligible": is_user_eligible,
            "windows": {}
        }

        if with_signature:
            response.update({
                "airdrop_window_rewards": rewards_awarded,
                "user_address": address,
                "airdrop_id": airdrop_id,
            })

        for window_data in windows_registration_data:
            window_info: Dict[str, Union[str, dict, None]] = {
                "claim_status": window_data.claim_status.value
            }

            if with_signature:
                registration_details = {}
                if window_data.registration_details:
                    rd = window_data.registration_details
                    registration_details = {
                        "registration_id": rd.registration_id,
                        "reject_reason": rd.reject_reason,
                        "registered_at": str(rd.registered_at),
                    }

                window_info["airdrop_window_claim_status"] = window_data.airdrop_window_claim_status.value \
                    if window_data.airdrop_window_claim_status else None
                window_info["registration_details"] = registration_details

            response["windows"][window_data.window_id] = window_info

        return response

    def generate_eligibility_response(
        self,
        airdrop_id: int,
        airdrop_window_id: int,
        address: str,
        is_user_eligible: bool,
        user_registered: bool,
        user_registration: UserRegistration,
        is_airdrop_window_claimed: bool,
        airdrop_claim_status: AirdropClaimStatus,
        rewards_awarded: int,
        is_claimable: bool
    ) -> dict:
        registration_id, reject_reason, registration_details = "", None, dict()

        if user_registered:
            registration_id = user_registration.receipt_generated
            reject_reason = user_registration.reject_reason
            registration_details = {
                "registration_id": user_registration.receipt_generated,
                "reject_reason": user_registration.reject_reason,
                "registered_at": str(user_registration.registered_at),
            }
        response = {
            "is_eligible": is_user_eligible,
            "is_already_registered": user_registered,
            "is_airdrop_window_claimed": is_airdrop_window_claimed,
            "airdrop_window_claim_status": airdrop_claim_status,
            "user_address": address,
            "airdrop_id": airdrop_id,
            "airdrop_window_id": airdrop_window_id,
            "reject_reason": reject_reason,
            "airdrop_window_rewards": rewards_awarded,
            "registration_id": registration_id,
            "is_claimable": is_claimable,
            "registration_details": registration_details
        }
        return response
