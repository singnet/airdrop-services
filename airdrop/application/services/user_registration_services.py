from datetime import datetime as dt
from http import HTTPStatus
from pydoc import locate

from jsonschema import validate, ValidationError
from web3 import Web3

from airdrop.config import AIRDROP_RECEIPT_SECRET_KEY_STORAGE_REGION, AIRDROP_RECEIPT_SECRET_KEY
from airdrop.constants import PROCESSOR_PATH, AirdropClaimStatus
from airdrop.constants import ELIGIBILITY_SCHEMA, USER_REGISTRATION_SCHEMA
from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_repository import UserRepository
from common.boto_utils import BotoUtils
from common.logger import get_logger
from common.utils import get_registration_receipt

logger = get_logger(__name__)


class UserRegistrationServices:
    @staticmethod
    def eligibility(inputs):
        status = HTTPStatus.BAD_REQUEST
        try:
            validate(instance=inputs, schema=ELIGIBILITY_SCHEMA)
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if airdrop is None:
                raise Exception("Airdrop id is not valid.")

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id,
                                                                                airdrop_id=airdrop_id)
            if airdrop_window is None:
                raise Exception("Airdrop window id is not valid.")

            airdrop_class = UserRegistrationServices.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            user_eligible_for_given_window = UserRepository(). \
                is_user_eligible_for_given_window(address, airdrop_id, airdrop_window_id)

            unclaimed_reward = UserRepository().get_unclaimed_reward(airdrop_id, address)

            is_user_eligible = airdrop_object.check_user_eligibility(user_eligible_for_given_window, unclaimed_reward)

            rewards_awarded = AirdropRepository().fetch_total_rewards_amount(airdrop_id, address)

            user_registered, user_registration = UserRepository(). \
                get_user_registration_details(address, airdrop_window_id)

            is_airdrop_window_claimed = False
            is_claimable = False
            airdrop_claim_status = AirdropWindowRepository().is_airdrop_window_claimed(airdrop_window_id, address)

            if airdrop_claim_status == AirdropClaimStatus.SUCCESS.value:
                is_airdrop_window_claimed = True
            else:
                if rewards_awarded > 0:
                    is_claimable = True
            # if the user has not claimed yet and there are rewards pending to be claimed , then let the user claim
            # rewards awarded will have some value ONLY when the claim window opens and the user has unclaimed rewards
            # a claim in progress ~ PENDING will also be considered as claimed ( we don't want the user to end up losing
            # gas in trying to claim again)
            registration_id, reject_reason, registration_details = "", None, dict()
            if user_registered:
                registration_id = user_registration.id
                reject_reason = user_registration.reject_reason
                registration_details = {
                    "registration_id": user_registration.id,
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
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response

    def register(self, inputs):
        try:
            validate(instance=inputs, schema=USER_REGISTRATION_SCHEMA)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()
            signature = inputs["signature"]
            block_number = inputs["block_number"]

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if not airdrop:
                raise Exception("Airdrop id is not valid.")

            airdrop_class = self.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            signature_verified, recovered_address, signature_details = self. \
                verify_signature(airdrop_object=airdrop_object, address=address, signature=signature,
                                 signature_parameters=inputs)
            if not signature_verified:
                raise Exception("Signature is not valid.")

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id)
            if airdrop_window is None:
                raise Exception("Airdrop window id is not valid.")
            is_registration_open = self.is_registration_window_open(airdrop_window.registration_start_period,
                                                                    airdrop_window.registration_end_period)
            if airdrop_window.registration_required and not is_registration_open:
                raise Exception("Airdrop window is not accepting registration at this moment.")

            user_eligible_for_given_window = UserRepository(). \
                is_user_eligible_for_given_window(address, airdrop_id, airdrop_window_id)

            unclaimed_reward = UserRepository().get_unclaimed_reward(airdrop_id, address)

            is_user_eligible = airdrop_object.check_user_eligibility(user_eligible_for_given_window, unclaimed_reward)
            if not is_user_eligible:
                raise Exception("Address is not eligible for this airdrop.")

            user_registered, user_registration = UserRepository(). \
                get_user_registration_details(address, airdrop_window_id)

            if user_registered:
                raise Exception("Address is already registered for this airdrop window")

            response = []
            if airdrop_object.register_all_window_at_once:
                airdrop_windows = AirdropWindowRepository().get_airdrop_windows(airdrop_id)
                for airdrop_window in airdrop_windows:
                    receipt = self.generate_user_registration_receipt(airdrop_id, airdrop_window.id, address)
                    UserRepository().register_user(airdrop_window.id, address, receipt, signature, signature_details,
                                                   block_number)
                    response.append({"airdrop_window_id": airdrop_window.id, "receipt": receipt})
            else:
                receipt = self.generate_user_registration_receipt(airdrop_id, airdrop_window_id, address)
                UserRepository().register_user(airdrop_window_id, address, receipt, signature, signature_details,
                                               block_number)
                # Keeping it backward compatible
                response = receipt
        except ValidationError as e:
            return HTTPStatus.BAD_REQUEST, repr(e)
        except BaseException as e:
            return HTTPStatus.BAD_REQUEST, repr(e)
        return HTTPStatus.OK, response

    def generate_user_registration_receipt(self, airdrop_id, airdrop_window_id, address):
        # Get the unique receipt to be issued , users can use this receipt as evidence that
        # registration was done
        secret_key = self.get_secret_key_for_receipt()
        receipt = get_registration_receipt(airdrop_id, airdrop_window_id, address, secret_key)
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

    @staticmethod
    def is_registration_window_open(start_period, end_period):
        now = dt.utcnow()
        if now > start_period or now < end_period:
            return True
        return False

    @staticmethod
    def verify_signature(airdrop_object, address, signature, signature_parameters):
        address = Web3.toChecksumAddress(address)
        signature = airdrop_object.trim_prefix_from_string_message(prefix="0x", message=signature)
        formatted_message = airdrop_object.format_signature_message(address, signature_parameters)
        signature_verified, recovered_address = airdrop_object.match_signature(address, formatted_message, signature)
        return signature_verified, recovered_address, formatted_message

    @staticmethod
    def load_airdrop_class(airdrop):
        if airdrop.airdrop_processor:
            airdrop_class = locate(f"{PROCESSOR_PATH}.{airdrop.airdrop_processor}")
        else:
            airdrop_class = DefaultAirdrop
        return airdrop_class
