
from eth_account.messages import encode_defunct
from jsonschema import validate, ValidationError
from datetime import datetime

import web3
from web3 import Web3
from eth_account.messages import defunct_hash_message, encode_defunct
from airdrop.config import NETWORK,AIRDROP_RECEIPT_SECRET_KEY_STORAGE_REGION, AIRDROP_RECEIPT_SECRET_KEY
from http import HTTPStatus
from airdrop.constants import AirdropClaimStatus
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_repository import UserRepository
from airdrop.domain.models.airdrop_window_eligibility import AirdropWindowEligibility
from common.boto_utils import BotoUtils
from common.utils import verify_signature, get_registration_receipt


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

            is_already_registered,registration_id = self.is_elgible_registered_user(
                airdrop_window_id, address)

            is_airdrop_window_claimed = False
            airdrop_claim_status = self.is_airdrop_window_claimed(
                airdrop_window_id, address)

            if airdrop_claim_status == AirdropClaimStatus.SUCCESS.value:
                is_airdrop_window_claimed = True

            reject_reason = None
            if not is_eligible_user:
                reject_reason = UserRepository().get_reject_reason(airdrop_window_id, address)

            response = AirdropWindowEligibility(airdrop_id, airdrop_window_id, address, is_eligible_user,
                                                is_already_registered, is_airdrop_window_claimed, airdrop_claim_status,
                                                reject_reason, rewards_awards, registration_id).to_dict()

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
                "required": ["signature", "address", "airdrop_id", "airdrop_window_id","block_number"],
            }

            validate(instance=inputs, schema=schema)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()
            signature = inputs["signature"]
            block_number = inputs["block_number"]

            verify_signature(airdrop_id, airdrop_window_id, address, signature, block_number)

            airdrop_window = self.get_user_airdrop_window(
                airdrop_id, airdrop_window_id
            )

            if airdrop_window is None:
                raise Exception(
                    "Airdrop window is not accepting registration at this moment"
                )

            is_eligible_user = self.check_user_eligibility(
                airdrop_id, airdrop_window_id, address)

            if not is_eligible_user:
                raise Exception(
                    "Address is not eligible for this airdrop"
                )

            is_registered_user, registration_id = self.is_elgible_registered_user(
                airdrop_window_id, address)

            if is_registered_user is False:
                # Get the unique receipt to be issued , users can use this receipt as evidence that
                # registration was done
                secret_key = self.get_secret_key_for_receipt()
                receipt = get_registration_receipt(airdrop_id,airdrop_window_id,address,secret_key)
                UserRepository().register_user(airdrop_window_id, address, receipt, signature, block_number)
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
        now = datetime.utcnow()
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
