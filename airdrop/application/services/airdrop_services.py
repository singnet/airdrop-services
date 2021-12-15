from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from jsonschema import validate, ValidationError
from http import HTTPStatus
from common.boto_utils import BotoUtils
from common.utils import generate_claim_signature, read_contract_address, get_transaction_receipt_from_blockchain
from airdrop.config import SIGNER_PRIVATE_KEY, SIGNER_PRIVATE_KEY_STORAGE_REGION, NETWORK_ID
from airdrop.constants import AIRDROP_ADDR_PATH, AirdropEvents, AirdropClaimStatus
from airdrop.domain.models.airdrop_claim import AirdropClaim
from airdrop.config import NUNET_TOKEN_ADDRESS


class AirdropServices:

    def airdrop_txn_watcher(self):

        pending_txns = AirdropRepository().get_pending_txns()

        for txn in pending_txns:
            try:
                txn_hash = txn.transaction_hash
                receipt = self.get_txn_receipt(txn_hash)
                if receipt is not None:
                    txn_hash_from_receipt = receipt.transactionHash
                    if receipt.status == 1:
                        txn_receipt_status = AirdropClaimStatus.SUCCESS.value
                    else:
                        txn_receipt_status = AirdropClaimStatus.FAILED.value
                    if(txn_hash_from_receipt == txn_hash):
                        AirdropRepository().update_txn_status(txn_hash_from_receipt, txn_receipt_status)
                    else:
                        airdrop_id = txn.airdrop_id
                        airdrop_window_id = txn.airdrop_window_id
                        user_address = txn.user_address
                        amount = txn.amount
                        AirdropRepository().airdrop_window_claim_txn(
                            airdrop_id, airdrop_window_id, user_address, txn_hash_from_receipt, amount)
                        print(
                            f"Transaction hash mismatch {txn_hash_from_receipt} {txn_hash}, creating new entry")

            except BaseException as e:
                print(f"Exception on Airdrop Txn Watcher {e}")

    def get_txn_receipt(self, txn_hash):
        try:
            return get_transaction_receipt_from_blockchain(txn_hash)
        except BaseException as e:
            print(f"Exception on get_txn_receipt {e}")
            raise e

    def airdrop_listen_to_events(self, event):
        event_data = event['data']
        event_name = event_data['event']

        if event_name == AirdropEvents.AIRDROP_CLAIM.value:
            return self.update_airdrop_window_claim_status(event_data)

    def update_airdrop_window_claim_status(self, event):
        try:
            event_payload = event['json_str']
            user_address = event_payload['claimer']
            amount = int(event_payload['amount'])
            airdrop_id = str(event_payload['airDropId'])
            airdrop_window_id = str(event_payload['airDropWindowId'])
            txn_hash = event['transactionHash']
            txn_status = AirdropClaimStatus.SUCCESS.value
            AirdropRepository().create_or_update_txn(
                airdrop_id, airdrop_window_id, user_address, txn_hash, txn_status, amount)
            return True
        except BaseException as e:
            print(f"Exception on Airdrop claim status update {e}")
            return False

    def airdrop_window_claim_history(self, inputs):
        status = HTTPStatus.BAD_REQUEST
        try:
            schema = {
                "type": "object",
                "properties": {"address": {"type": "string"}, "airdrop_id": {"type": "string"}},
                "required": ["address", "airdrop_id"],
            }

            validate(instance=inputs, schema=schema)

            user_address = inputs["address"]
            airdrop_id = inputs["airdrop_id"]

            claim_history = AirdropRepository().airdrop_window_claim_history(
                airdrop_id, user_address)

            response = {"claim_history": claim_history}
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window History {e}")
            response = str(e)

        return status, response

    def airdrop_window_claim_status(self, inputs):
        status = HTTPStatus.BAD_REQUEST
        try:
            schema = {
                "type": "object",
                "properties": {"address": {"type": "string"}, "airdrop_id": {"type": "string"}, "airdrop_window_id": {"type": "string"}, "txn_hash": {"type": "string"}, "amount": {"type": "string"}},
                "required": ["address", "airdrop_id", "airdrop_window_id", "txn_hash", "amount"],
            }

            validate(instance=inputs, schema=schema)

            user_address = inputs["address"]
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            txn_hash = inputs["txn_hash"]
            amount = inputs["amount"]

            AirdropRepository().airdrop_window_claim_txn(
                airdrop_id, airdrop_window_id, user_address, txn_hash, amount)

            response = HTTPStatus.OK.phrase
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window Claim {e}")
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

            claimable_amount, token_address = AirdropRepository().get_airdrop_window_claimable_amount(
                airdrop_id, airdrop_window_id, user_address)

            signature = self.get_signature_for_airdrop_window_id(
                claimable_amount, airdrop_id, airdrop_window_id, user_address)

            response = AirdropClaim(airdrop_id,
                                    airdrop_window_id, user_address, signature, claimable_amount, token_address).to_dict()

            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window Claim {e}")
            response = str(e)

        return status, response

    def get_signature_for_airdrop_window_id(self, amount, airdrop_id, airdrop_window_id, user_address):
        try:

            contract_address = AirdropRepository().get_contract_address(airdrop_id)

            # TODO: Read from database address & rename column to token address
            token_address = NUNET_TOKEN_ADDRESS

            boto_client = BotoUtils(
                region_name=SIGNER_PRIVATE_KEY_STORAGE_REGION)
            private_key = boto_client.get_parameter_value_from_secrets_manager(
                secret_name=SIGNER_PRIVATE_KEY)

            return generate_claim_signature(
                amount, airdrop_id, airdrop_window_id, user_address, contract_address, token_address, private_key)

        except BaseException as e:
            raise e

    def get_airdrops_schedule(self, token_address):
        status = HTTPStatus.BAD_REQUEST

        try:
            response = AirdropRepository().get_airdrops_schedule(token_address)
            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response
