from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from jsonschema import validate, ValidationError
from http import HTTPStatus
from common.boto_utils import BotoUtils
from common.utils import generate_claim_signature, read_contract_address
from airdrop.config import SIGNER_PRIVATE_KEY, SIGNER_PRIVATE_KEY_STORAGE_REGION, NETWORK_ID
from airdrop.constants import AIRDROP_ADDR_PATH
from airdrop.domain.models.airdrop_claim import AirdropClaim


class AirdropServices:

    def airdrop_window_claim_status(self, inputs):
        status = HTTPStatus.BAD_REQUEST
        try:
            schema = {
                "type": "object",
                "properties": {"address": {"type": "string"}, "airdrop_id": {"type": "string"}, "airdrop_window_id": {"type": "string"}, "txn_status": {"type": "string"}, "txn_hash": {"type": "string"}, "amount": {"type": "string"}},
                "required": ["address", "airdrop_id", "airdrop_window_id", "txn_status", "txn_hash", "amount"],
            }

            validate(instance=inputs, schema=schema)

            user_address = inputs["address"]
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            txn_hash = inputs["txn_hash"]
            txn_status = inputs["txn_status"]
            amount = inputs["amount"]

            AirdropRepository().airdrop_window_claim_txn(
                airdrop_id, airdrop_window_id, user_address, txn_hash, txn_status, amount)

            response = HTTPStatus.OK.phrase
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response

    def airdrop_window_claims(self, inputs):
        status = HTTPStatus.BAD_REQUEST
        try:

            schema = {
                "type": "object",
                "properties": {"address": {"type": "string"}, "airdrop_id": {"type": "string"}, "airdrop_window_id": {"type": "string"}},
                "required": ["address", "airdrop_id", "airdrop_window_id"],
            }

            validate(instance=inputs, schema=schema)

            user_address = inputs["address"]
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]

            airdrop_repo = AirdropRepository()
            airdrop_repo.is_claimed_airdrop_window(
                user_address, airdrop_window_id)

            claimable_amount = AirdropRepository().get_airdrop_window_claimable_amount(
                airdrop_id, airdrop_window_id, user_address)

            signature = self.get_signature_for_airdrop_window_id(
                claimable_amount, airdrop_id, airdrop_window_id, user_address)

            response = AirdropClaim(airdrop_id,
                                    airdrop_window_id, user_address, signature, claimable_amount).to_dict()

            status = HTTPStatus.OK
            return status, response
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response

    def get_signature_for_airdrop_window_id(self, amount, airdrop_id, airdrop_window_id, user_address):
        try:

            contract_address = read_contract_address(net_id=NETWORK_ID, path=AIRDROP_ADDR_PATH,
                                                     key='address')

            token_address = AirdropRepository().get_token_address(airdrop_id)

            boto_client = BotoUtils(
                region_name=SIGNER_PRIVATE_KEY_STORAGE_REGION)
            private_key = boto_client.get_parameter_value_from_secrets_manager(
                secret_name=SIGNER_PRIVATE_KEY)

            return generate_claim_signature(
                amount, airdrop_id, airdrop_window_id, user_address, contract_address, token_address, private_key)

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
