import json
from typing import Dict, List, Tuple, Union
from web3 import Web3

from airdrop.constants import AirdropClaimStatus
from airdrop.infrastructure.models import AirdropWindow, UserRegistration
from airdrop.application.types.windows import WindowRegistrationData
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.balance_snapshot import UserBalanceSnapshotRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.utils import Utils
from airdrop.config import RejuveAirdropConfig
from common.logger import get_logger
from common.utils import (
    get_registration_receipt_cardano,
    get_registration_receipt_ethereum
)
from infrastructure.repositories.airdrop_repository import AirdropRepository

logger = get_logger(__name__)


class RejuveAirdrop(DefaultAirdrop):

    def __init__(self, airdrop_id, airdrop_window_id=None):
        super().__init__(airdrop_id, airdrop_window_id)
        self.domain_name = "Rejuve Airdrop"
        self.register_all_window_at_once = False
        self.allow_update_registration = True
        self.is_claim_signature_required = True
        self.chain_context = {
            "deposit_address": RejuveAirdropConfig.deposit_address.value,
            "amount": RejuveAirdropConfig.pre_claim_transfer_amount.value["amount"],
            "chain": RejuveAirdropConfig.chain.value
        }

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
        block_number: int,
        wallet_name: str,
    ) -> dict:
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

    def match_signature(
        self,
        address: str,
        signature: str,
        block_number: int,
        wallet_name: str,
        key: str | None,
    ) -> dict:
        utils = Utils()
        network = self.recognize_blockchain_network(address)
        logger.info(f"Start of signature matching | address={address}, signature={signature}, network={network}")

        if network not in {"Ethereum", "Cardano"}:
            raise ValueError(f"Unsupported network: {network}")

        if network == "Ethereum":
            address = Web3.to_checksum_address(address)
        elif network == "Cardano" and key is None:
            raise ValueError("Key must be provided for Cardano signatures.")

        formatted_message = self.format_user_registration_signature_message(
            address,
            block_number=block_number,
            wallet_name=wallet_name
        )
        message = json.dumps(formatted_message, separators=(',', ':'))

        sign_verified = (
            utils.match_ethereum_signature_eip191(address, message, signature)
            if network == "Ethereum"
            else utils.match_cardano_signature(message, signature, key)
        )

        if not sign_verified:
            logger.error("Invalid signature")
            raise ValueError("Signature is not valid.")

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

    def register(self, data: dict) -> list | str:
        logger.info(f"Starting the registration process for {self.__class__.__name__}")
        address = data["address"].lower()
        signature = data["signature"]
        block_number = data["block_number"]
        wallet_name = data["wallet_name"]
        key = data.get("key")

        registration_repo = UserRegistrationRepository()
        airdrop_window_repo = AirdropWindowRepository()
        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)

        formatted_message = self.match_signature(
            address=address,
            signature=signature,
            block_number=block_number,
            wallet_name=wallet_name,
            key=key,
        )

        is_registration_open = self.is_phase_window_open(
            airdrop_window.registration_start_period,
            airdrop_window.registration_end_period
        )
        if airdrop_window.registration_required and not is_registration_open:
            logger.error("Airdrop window is not accepting registration at this moment")
            raise Exception("Airdrop window is not accepting registration at this moment")

        is_user_eligible = self.check_user_eligibility(address=address)
        if not is_user_eligible:
            logger.error("Address is not eligible for this airdrop")
            raise Exception("Address is not eligible for this airdrop")

        user_registered, _ = registration_repo. \
            get_user_registration_details(address, self.window_id)
        if user_registered:
            logger.error("Address is already registered for this airdrop window")
            raise Exception("Address is already registered for this airdrop window")

        receipt = self.generate_user_registration_receipt(self.id, self.window_id, address)
        registration_repo.register_user(
            self.window_id,
            address,
            receipt,
            signature,
            formatted_message,
            block_number
        )

        return receipt

    def update_registration(self, data: dict):
        """
        Update the user's registration details for a specific airdrop window.

        Steps:
        1. Validate the airdrop window exists.
        2. Check if claim phase is open.
        3. Check if the user is eligible for the airdrop.
        4. Match the provided signature to confirm identity.
        5. Ensure the user is already registered.
        6. Generate new receipt.
        7. Update the registration with new signature details.
        """
        logger.info(f"Starting registration update process for {self.__class__.__name__}")

        address = data["address"].lower()
        signature = data["signature"]
        reward_address = data["reward_address"]
        block_number = data["block_number"]
        wallet_name = data["wallet_name"]
        key = data["key"]

        registration_repo = UserRegistrationRepository()
        airdrop_window_repo = AirdropWindowRepository()

        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)
        if not airdrop_window:
            raise Exception(f"Airdrop window does not exist: {self.window_id}")

        if not self.is_phase_window_open(
            airdrop_window.claim_start_period,
            airdrop_window.claim_end_period
        ):
            raise Exception("Airdrop window is not accepting claim at this moment")

        if not self.check_user_eligibility(address=address):
            logger.error(f"Address {address} is not eligible for airdrop in window {self.window_id}")
            raise Exception("Address is not eligible for this airdrop.")

        signature_details = self.match_signature(
            address=reward_address,
            signature=signature,
            block_number=block_number,
            wallet_name=wallet_name,
            key=key
        )

        user_registered, _ = registration_repo.get_user_registration_details(address, self.window_id)
        if not user_registered:
            logger.error(f"Address {address} is not registered for window {self.window_id}")
            raise Exception("Address is not registered for this airdrop window.")

        receipt = self.generate_user_registration_receipt(self.id, self.window_id, reward_address)

        registration_repo.update_registration(
            airdrop_window_id=self.window_id,
            address=address,
            signature_details=signature_details,
            receipt=receipt
        )

    def generate_multiple_windows_eligibility_response(
        self,
        is_user_eligible: bool,
        airdrop_id: int,
        address: str,
        windows_registration_data: List[WindowRegistrationData],
        rewards_awarded: int,
        with_signature: bool,
    ) -> dict:
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

    def get_claimable_amount(self, user_address: str) -> Tuple[int, int]:
        airdrop_window_repo = AirdropRepository()
        claimable_amount = airdrop_window_repo.fetch_total_rewards_amount(self.id, user_address, airdrop_class="RejuveAirdrop")
        total_eligible_amount = airdrop_window_repo.fetch_total_eligibility_amount(self.id, user_address)

        if claimable_amount == 0:
            raise Exception("Airdrop Already claimed / pending")

        return claimable_amount, total_eligible_amount
