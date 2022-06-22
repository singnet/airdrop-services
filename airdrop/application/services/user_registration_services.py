from eth_account.messages import encode_defunct
from jsonschema import validate, ValidationError
from datetime import datetime as dt

import web3
from web3 import Web3
from py_eth_sig_utils.signing import recover_typed_data, signature_to_v_r_s
from airdrop.config import NETWORK, AIRDROP_RECEIPT_SECRET_KEY_STORAGE_REGION, AIRDROP_RECEIPT_SECRET_KEY
from http import HTTPStatus
from airdrop.constants import AirdropClaimStatus, USER_REGISTRATION_SIGNATURE_FORMAT
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_repository import UserRepository
from airdrop.domain.models.airdrop_window_eligibility import AirdropWindowEligibility
from common.boto_utils import BotoUtils
from common.utils import verify_signature, get_registration_receipt
from common.logger import get_logger

logger = get_logger(__name__)


class UserRegistrationServices:

    def eligibility(self, inputs):

        status = HTTPStatus.BAD_REQUEST

        try:
            schema = {
                "type": "object",
                "properties": {
                    "address": {"type": "string"}
                },
                "required": ["address", "airdrop_id", "airdrop_window_id"],
            }

            validate(instance=inputs, schema=schema)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()

            airdrop_window = AirdropWindowRepository(
            ).get_airdrop_window_by_id(airdrop_window_id)

            if airdrop_window is None:
                raise Exception("Invalid Airdrop window id")

            is_eligible_user, rewards_awards = self.check_user_eligibility(
                user_address=address, airdrop_id=airdrop_id, airdrop_window_id=airdrop_window_id)

            is_already_registered, registration_id = self.is_elgible_registered_user(
                airdrop_window_id, address)

            is_airdrop_window_claimed = False
            airdrop_claim_status = self.is_airdrop_window_claimed(
                airdrop_window_id, address)

            if airdrop_claim_status == AirdropClaimStatus.SUCCESS.value:
                is_airdrop_window_claimed = True
            is_claimable = False
            # if the user has not claimed yet and there are rewards pending to be claimed , then let the user claim
            # rewards awarded will have some value ONLY when the claim window opens and the user has unclaimed rewards
            # a claim in progress ~ PENDING will also be considered as claimed ( we don't want the user to end up losing
            # gas in trying to claim again)
            if is_airdrop_window_claimed is False and rewards_awards > 0:
                is_claimable = True
            reject_reason = None
            if not is_eligible_user:
                reject_reason = UserRepository().get_reject_reason(airdrop_window_id, address)

            response = AirdropWindowEligibility(airdrop_id, airdrop_window_id, address, is_eligible_user,
                                                is_already_registered, is_airdrop_window_claimed, airdrop_claim_status,
                                                reject_reason, rewards_awards, registration_id, is_claimable).to_dict()

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
        message = {
            "Airdrop": {
                "airdropId": airdrop_id,
                "airdropWindowId": airdrop_window_id,
                "blockNumber": block_number,
                "walletAddress": address,
            },
        }
        if cardano_address:
            message["Airdrop"]["cardanoAddress"] = "addr_test1qqera830frgpvw9f0jj2873lwe8nd8vcsf0q0ftuqqgd9g8ucaczw4" \
                                                   "27uq8y7axn2v3w8dua87kjgdgurmgl38vd2hysk4dfj9"
        formatted_message = USER_REGISTRATION_SIGNATURE_FORMAT
        formatted_message["message"] = message
        recovered_address = recover_typed_data(formatted_message, *signature_to_v_r_s(bytes.fromhex(signature)))
        if recovered_address.lower() != address.lower():
            logger.info(f"INVALID SIGNATURE {signature}")
            logger.info(f"For airdrop_id:{airdrop_id} , airdrop_window_id:{airdrop_window_id} , address:{address} , "
                        f"block_number{block_number}")
        return formatted_message, recovered_address
