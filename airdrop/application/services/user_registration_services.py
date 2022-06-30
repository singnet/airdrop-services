from datetime import datetime as dt
from http import HTTPStatus

from jsonschema import validate, ValidationError
from py_eth_sig_utils.signing import recover_typed_data, signature_to_v_r_s
from web3 import Web3

from airdrop.config import AIRDROP_RECEIPT_SECRET_KEY_STORAGE_REGION, AIRDROP_RECEIPT_SECRET_KEY
from airdrop.constants import AirdropClaimStatus, USER_REGISTRATION_SIGNATURE_FORMAT
from airdrop.constants import ELIGIBILITY_SCHEMA
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

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id)

            if airdrop_window is None:
                raise Exception("Invalid Airdrop window id")

            user_eligible_for_given_window = UserRepository(). \
                is_user_eligible_for_given_window(address, airdrop_id, airdrop_window_id)

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

            if user_registered:
                registration_id = user_registration.registration_id
                reject_reason = user_registration.reject_reason
                registration_details = {
                    "registration_id": user_registration.registration_id,
                    "reject_reason": user_registration.reject_reason,
                    "other_details": user_registration.signed_data.get("message", {}),
                    "registered_at": user_registration.registered_at
                }
            else:
                registration_id, reject_reason, registration_details = "", None, dict()
            response = {
                "is_eligible": user_eligible_for_given_window,
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

        status = HTTPStatus.BAD_REQUEST

        try:
            schema = {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "signature": {"type": "string"},
                },
                "required": ["signature", "address", "airdrop_id", "airdrop_window_id", "block_number"],
            }

            validate(instance=inputs, schema=schema)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()
            cardano_address = inputs.get("cardano_address", None)
            signature = inputs["signature"]
            block_number = inputs["block_number"]

            signed_data, recovered_address = self.verify_signature(
                signature=signature, airdrop_id=airdrop_id, airdrop_window_id=airdrop_window_id,
                block_number=block_number, address=address, cardano_address=cardano_address)

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id)
            if airdrop_window is None:
                raise Exception("Airdrop window id is invalid.")

            registration_required = airdrop_window.registration_required
            if registration_required:
                now = dt.utcnow()
                registration_start_period = airdrop_window.registration_start_period
                registration_end_period = airdrop_window.registration_end_period
                if now < registration_start_period or now > registration_end_period:
                    raise Exception("Airdrop window is not accepting registration at this moment.")

            is_eligible_user = self.check_user_eligibility(airdrop_id, airdrop_window_id, address)

            if not is_eligible_user:
                raise Exception("Address is not eligible for this airdrop")

            is_registered_user, registration_id = self.is_elgible_registered_user(airdrop_window_id, address)

            if is_registered_user is False:
                # Get the unique receipt to be issued , users can use this receipt as evidence that
                # registration was done
                secret_key = self.get_secret_key_for_receipt()
                receipt = get_registration_receipt(airdrop_id, airdrop_window_id, address, secret_key)
                UserRepository().register_user(airdrop_window_id, address, receipt, signature, signed_data,
                                               block_number)
                response = receipt
            else:
                raise Exception(
                    "Address is already registered for this airdrop window"
                )

            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response

    def get_secret_key_for_receipt(self):
        try:
            boto_client = BotoUtils(
                region_name=AIRDROP_RECEIPT_SECRET_KEY_STORAGE_REGION)
            private_key = boto_client.get_parameter_value_from_secrets_manager(
                secret_name=AIRDROP_RECEIPT_SECRET_KEY)

            return private_key

        except BaseException as e:
            raise e

    def get_user_airdrop_window(self, airdrop_id, airdrop_window_id):
        now = dt.utcnow()
        return AirdropWindowRepository().is_open_airdrop_window(
            airdrop_id, airdrop_window_id, now
        )

    def is_elgible_registered_user(self, airdrop_window_id, address):
        return UserRepository().is_registered_user(
            airdrop_window_id, address
        )

    def is_airdrop_window_claimed(self, airdrop_window_id, address):
        return AirdropWindowRepository().is_airdrop_window_claimed(
            airdrop_window_id, address
        )

    def check_user_eligibility(self, airdrop_id, airdrop_window_id, user_address):
        return UserRepository().check_rewards_awarded(airdrop_id, airdrop_window_id, user_address)

    def verify_signature(self, signature, airdrop_id, airdrop_window_id, block_number, address, cardano_address=None):
        address = Web3.toChecksumAddress(address)
        if signature.startswith("0x"):
            signature = signature[2:]
        message = {
            "Airdrop": {
                "airdropId": airdrop_id,
                "airdropWindowId": airdrop_window_id,
                "blockNumber": block_number,
                "walletAddress": address,
            },
        }
        formatted_message = USER_REGISTRATION_SIGNATURE_FORMAT
        if cardano_address:
            formatted_message["types"]["AirdropSignatureTypes"].append({"name": "cardanoAddress", "type": "string"})
            message["Airdrop"]["cardanoAddress"] = cardano_address
        formatted_message["message"] = message
        recovered_address = recover_typed_data(formatted_message, *signature_to_v_r_s(bytes.fromhex(signature)))
        if recovered_address.lower() != address.lower():
            logger.info(f"INVALID SIGNATURE {signature}")
            logger.info(f"For airdrop_id:{airdrop_id} , airdrop_window_id:{airdrop_window_id} , address:{address} , "
                        f"block_number{block_number}")
        return formatted_message, recovered_address
