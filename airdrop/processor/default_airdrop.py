from datetime import timezone
import inspect
from web3 import Web3

from airdrop.constants import USER_REGISTRATION_SIGNATURE_DEFAULT_FORMAT, AirdropClaimStatus
from airdrop.config import NUNET_SIGNER_PRIVATE_KEY
from airdrop.infrastructure.models import AirdropWindow, UserRegistration
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.processor.base_airdrop import BaseAirdrop
from airdrop.utils import Utils, datetime_in_utcnow
from common.exceptions import RequiredDataNotFound
from common.logger import get_logger

logger = get_logger(__name__)


class DefaultAirdrop(BaseAirdrop):

    def __init__(self, airdrop_id, airdrop_window_id=None):
        super().__init__(airdrop_id, airdrop_window_id)
        self.domain_name = "Nunet Airdrop"
        self.is_claim_signature_required = True
        self.claim_signature_data_format = ["string", "uint256", "uint256", "address",
                                            "uint256", "uint256", "address", "address"]
        self.claim_signature_private_key_secret = NUNET_SIGNER_PRIVATE_KEY

    def check_user_eligibility(self, address: str) -> bool:
        if not isinstance(address, str):
            raise Exception("The address was sent in the wrong format.")

        address = address.lower()
        registration_repo = UserRegistrationRepository()
        user_eligible_for_given_window = registration_repo.is_user_eligible_for_given_window(
            address, self.id, self.window_id
        )

        return user_eligible_for_given_window

    def format_user_registration_signature_message(self, address: str, signature_parameters: dict) -> dict:
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

    def format_and_get_claim_signature_details(self, **kwargs) -> tuple[list, list]:
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

    def match_signature(self, data: dict) -> dict:
        address = data["address"].lower()
        checksum_address = Web3.to_checksum_address(address)
        signature = data["signature"]
        logger.info(f"Start of the signature matching for {address = }, {signature = }")
        utils = Utils()
        formatted_message = self.format_user_registration_signature_message(checksum_address, data)
        formatted_signature = utils.trim_prefix_from_string_message(prefix="0x", message=signature)
        sign_verified, _ = utils.match_ethereum_signature_eip712(address, formatted_message, formatted_signature)
        if not sign_verified:
            logger.error("Signature is not valid")
            raise Exception("Signature is not valid")
        logger.info("Signature validity confirmed")
        return formatted_message

    def generate_multiple_windows_eligibility_response(self, **kwargs):
        pass

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
                "other_details": user_registration.signature_details.get("message", {}).get("Airdrop", {}),
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

    def register(self, data: dict) -> list | str:
        logger.info(f"Starting the registration process for {self.__class__.__name__}")
        address = data["address"].lower()
        signature = data["signature"]
        block_number = data["block_number"]

        registration_repo = UserRegistrationRepository()
        airdrop_window_repo = AirdropWindowRepository()
        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)

        formatted_message = self.match_signature(data)

        is_registration_open = self.is_registration_window_open(airdrop_window.registration_start_period,
                                                                airdrop_window.registration_end_period)
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

        response = []
        if self.register_all_window_at_once:
            airdrop_windows = airdrop_window_repo.get_airdrop_windows(self.id)
            for window in airdrop_windows:
                receipt = self.generate_user_registration_receipt(self.id, window.id, address)
                registration_repo.register_user(window.id, address, receipt, signature,
                                                formatted_message, block_number)
                response.append({"airdrop_window_id": window.id, "receipt": receipt})
        else:
            receipt = self.generate_user_registration_receipt(self.id, self.window_id, address)
            registration_repo.register_user(self.window_id, address, receipt, signature,
                                            formatted_message, block_number)
            # Keeping it backward compatible
            response = receipt

        return response

    def update_registration(self, data: dict) -> list | str:
        logger.info(f"Starting the registration updating process for {self.__class__.__name__}")
        address = data["address"].lower()
        signature = data["signature"]
        block_number = data["block_number"]

        airdrop_window_repo = AirdropWindowRepository()
        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)

        formatted_message = self.match_signature(data)

        if not self.allow_update_registration:
            raise Exception("Registration update not allowed.")

        airdrop_windows: list[AirdropWindow] = airdrop_window_repo.get_airdrop_windows(self.id) \
            if self.register_all_window_at_once \
            else [airdrop_window]

        response = []
        registration_repo = UserRegistrationRepository()
        utc_now = datetime_in_utcnow()
        for window in airdrop_windows:
            try:
                is_registered, receipt = registration_repo.is_registered_user(window.id, address)
                is_claimed = airdrop_window_repo.is_airdrop_window_claimed(window.id, address)
                assert is_registered, "not registered"
                assert not is_claimed, "already claimed"
                claim_end_period = window.claim_end_period
                if claim_end_period.tzinfo is None:
                    claim_end_period = claim_end_period.replace(tzinfo=timezone.utc)
                assert claim_end_period > utc_now, "claim period is over"
                registration_repo.update_registration(window.id, address,
                                                      signature=signature,
                                                      signature_details=formatted_message,
                                                      block_number=block_number,
                                                      registered_at=utc_now)
                response.append({"airdrop_window_id": window.id, "receipt": receipt})
            except AssertionError as e:
                warning = f"Airdrop window {window.id} registration update failed ({str(e)})"
                if len(airdrop_windows) == 1 and window == airdrop_window:
                    raise Exception(warning)
                response.append({"airdrop_window_id": window.id, "warning": warning})

        return response
