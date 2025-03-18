from airdrop.infrastructure.models import AirdropWindow
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.constants import (USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT,
                               USER_CLAIM_SIGNATURE_DEFAULT_FORMAT)
from airdrop.config import LoyaltyAirdropConfig
from common.logger import get_logger

logger = get_logger(__name__)


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

    def format_user_registration_signature_message(
        self,
        address: str,
        block_number: int,
        cardano_address: str,
        cardano_wallet_name: str
    ) -> dict:
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

    def register(self, data: dict) -> list | str:
        logger.info(f"Starting the registration process for {self.__class__.__name__}")
        address = data["address"].lower()
        signature = data["signature"]
        block_number = data["block_number"]
        cardano_address = data["cardano_addres"]
        cardano_wallet_name = data["cardano_wallet_name"]

        registration_repo = UserRegistrationRepository()
        airdrop_window_repo = AirdropWindowRepository()
        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)

        formatted_message = self.match_signature(
            address=address,
            signature=signature,
            block_number=block_number,
            cardano_address=cardano_address,
            cardano_wallet_name=cardano_wallet_name
        )

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
        cardano_address = data["cardano_addres"]
        cardano_wallet_name = data["cardano_wallet_name"]

        airdrop_window_repo = AirdropWindowRepository()
        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)

        formatted_message = self.match_signature(
            address=address,
            signature=signature,
            block_number=block_number,
            cardano_address=cardano_address,
            cardano_wallet_name=cardano_wallet_name
        )

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
