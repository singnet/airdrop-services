from http import HTTPStatus
from jsonschema import validate, ValidationError
from datetime import datetime
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWIndowRepository
from airdrop.infrastructure.repositories.user_repository import UserRepository
from airdrop.config import AirdropStrategy
from common.utils import verify_signature


class UserRegistrationServices:

    def eligibility(self, inputs):

        status = HTTPStatus.BAD_REQUEST

        try:
            schema = {
                "type": "object",
                "properties": {
                    "airdrop_window_id": {"type": "string"},
                    "airdrop_id": {"type": "string"},
                    "address": {"type": "string"},
                    "signature": {"type": "string"},
                },
                "required": ["signature", "address", "airdrop_id", "airdrop_window_id"],
            }

            validate(instance=inputs, schema=schema)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()
            signature = inputs["signature"]

            airdrop_window = self.get_user_airdrop_window(
                airdrop_id, airdrop_window_id
            )

            if airdrop_window is None:
                raise Exception(
                    "Airdrop window is not accepting registration at this moment"
                )

            is_eligible_user = self.check_user_eligibility(
                'AGIX', address)

            if not is_eligible_user:
                raise Exception(
                    "Address is not eligible for this airdrop"
                )

            response = 'Address is eligible for Airdrop'
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
                    "airdrop_window_id": {"type": "string"},
                    "airdrop_id": {"type": "string"},
                    "address": {"type": "string"},
                    "signature": {"type": "string"},
                },
                "required": ["signature", "address", "airdrop_id", "airdrop_window_id"],
            }

            validate(instance=inputs, schema=schema)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()
            signature = inputs["signature"]

            # verify_signature(airdrop_id, airdrop_window_id, address, signature)

            airdrop_window = self.get_user_airdrop_window(
                airdrop_id, airdrop_window_id
            )

            if airdrop_window is None:
                raise Exception(
                    "Airdrop window is not accepting registration at this moment"
                )

            is_eligible_user = self.check_user_eligibility(
                'AGIX', address)

            if not is_eligible_user:
                raise Exception(
                    "Address is not eligible for this airdrop"
                )

            is_registered_user = self.is_elgible_registered_user(
                airdrop_window_id, address)

            if is_registered_user is not None:
                raise Exception(
                    "Address is already registered for this airdrop window")

            UserRepository().register_user(airdrop_window_id, address)

            response = 'Address registered for Airdrop'
            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response

    def get_user_airdrop_window(self, airdrop_id, airdrop_window_id):
        now = datetime.utcnow()
        return AirdropWIndowRepository().is_open_airdrop_window(
            airdrop_id, airdrop_window_id, now
        )

    def is_elgible_registered_user(self, airdrop_window_id, address):
        return UserRepository().is_registered_user(
            airdrop_window_id, address
        )

    def check_user_eligibility(self, token, address):
        try:
            if(token == AirdropStrategy.AGIX):
                return self.check_agix_airdrop_eligibility(address)
        except:
            raise Exception(
                "Invalid Airdrop"
            )

    def check_agix_airdrop_eligibility(self, address):
        # TODO: Implement user eligibility check for AGIX airdrop
        return True
