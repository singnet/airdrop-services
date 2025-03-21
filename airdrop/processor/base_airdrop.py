from abc import ABC, abstractmethod
from datetime import timezone
from typing import Tuple, Optional

from airdrop.config import AIRDROP_RECEIPT_SECRET_KEY, AIRDROP_RECEIPT_SECRET_KEY_STORAGE_REGION
from airdrop.utils import datetime_in_utcnow
from common.boto_utils import BotoUtils
from common.logger import get_logger
from common.utils import get_registration_receipt_ethereum

logger = get_logger(__name__)


class BaseAirdrop(ABC):
    @abstractmethod
    def __init__(self, airdrop_id: int, airdrop_window_id: Optional[int] = None):
        self.domain_name = "Base Airdrop"
        self.id = airdrop_id
        self.window_id = airdrop_window_id
        self.register_all_window_at_once = False
        self.allow_update_registration = False
        self.is_claim_signature_required = False
        self.chain_context = {}
        self.reward_processor_name = ""

    @abstractmethod
    def format_user_registration_signature_message(self, **kwargs) -> dict:
        pass

    @abstractmethod
    def format_and_get_claim_signature_details(self, **kwargs) -> tuple[list, list]:
        pass

    @staticmethod
    def is_phase_window_open(start_period, end_period) -> bool:
        now = datetime_in_utcnow()

        if start_period.tzinfo is None:
            start_period = start_period.replace(tzinfo=timezone.utc)
        if end_period.tzinfo is None:
            end_period = end_period.replace(tzinfo=timezone.utc)

        if now > start_period and now < end_period:
            return True
        return False

    def generate_user_registration_receipt(self, airdrop_id: int,
                                           window_id: int, address: str) -> str:
        # Get the unique receipt to be issued , users can use this receipt as evidence that
        # registration was done
        logger.info("Generate user registration receipt")
        secret_key = self.get_secret_key_for_receipt()
        receipt = get_registration_receipt_ethereum(airdrop_id, window_id, address, secret_key)
        return receipt

    @staticmethod
    def get_secret_key_for_receipt():
        boto_client = BotoUtils(region_name=AIRDROP_RECEIPT_SECRET_KEY_STORAGE_REGION)
        try:
            private_key = boto_client. \
                get_parameter_value_from_secrets_manager(secret_name=AIRDROP_RECEIPT_SECRET_KEY)
        except BaseException as e:
            raise e
        return private_key

    @abstractmethod
    def register(self, **kwargs) -> list | str:
        pass

    @abstractmethod
    def update_registration(self, **kwargs) -> list:
        pass

    @abstractmethod
    def generate_multiple_windows_eligibility_response(self, **kwargs) -> list:
        pass

    @abstractmethod
    def check_user_eligibility(self, *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def match_signature(self, *args, **kwargs) -> dict:
        pass

    @abstractmethod
    def generate_eligibility_response(self, **kwargs):
        pass

    @abstractmethod
    def get_claimable_amount(self, **kwargs) -> Tuple[int, int]:
        pass

    @abstractmethod
    def validate_deposit_event(self, **kwargs) -> dict:
        pass