from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from jsonschema import validate, ValidationError
from http import HTTPStatus
from common.boto_utils import BotoUtils
from common.utils import generate_claim_signature, get_contract_address
from airdrop.config import SIGNER_PRIVATE_KEY, SIGNER_PRIVATE_KEY_STORAGE_REGION


class AirdropServices:

    def get_signature_for_airdrop_window_id(self, amount, airdrop_id, airdrop_window_id, address):
        try:
            boto_client = BotoUtils(
                region_name=SIGNER_PRIVATE_KEY_STORAGE_REGION)
            private_key = boto_client.get_parameter_value_from_secrets_manager(
                secret_name=SIGNER_PRIVATE_KEY)

            contract_address = get_contract_address()

            return generate_claim_signature(amount, airdrop_id, airdrop_window_id, address, contract_address, private_key)

        except BaseException as e:
            raise str(e)

    def get_airdrops(self, inputs):
        status = HTTPStatus.BAD_REQUEST

        try:
            schema = {
                "type": "object",
                "properties": {"limit": {"type": "string"}, "skip": {"type": "string"}},
                "required": ["limit", "skip"],
            }

            validate(instance=inputs, schema=schema)

            skip = inputs["skip"]
            limit = inputs["limit"]

            airdrops = AirdropRepository().get_airdrops(limit, skip)
            response = {"airdrops": airdrops}
            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response

    def get_airdrops_schedule(self, inputs):
        status = HTTPStatus.BAD_REQUEST

        try:
            schema = {
                "type": "object",
                "properties": {"limit": {"type": "string"}, "skip": {"type": "string"}},
                "required": ["limit", "skip"],
            }

            validate(instance=inputs, schema=schema)

            skip = inputs["skip"]
            limit = inputs["limit"]

            schedule = AirdropRepository().get_airdrops_schedule(limit, skip)
            response = {"schedule": schedule}
            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response
