from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from jsonschema import validate, ValidationError
from http import HTTPStatus
from common.boto_utils import BotoUtils
from common.utils import generate_claim_signature, read_contract_address, get_transaction_receipt_from_blockchain
from airdrop.config import SIGNER_PRIVATE_KEY, SIGNER_PRIVATE_KEY_STORAGE_REGION, NETWORK_ID
from airdrop.constants import AIRDROP_ADDR_PATH, AirdropEvents, AirdropClaimStatus
from airdrop.domain.models.airdrop_claim import AirdropClaim
from airdrop.domain.models.airdrop_stake_claim_details import AirdropStakeClaimDetails


class AirdropServices:

    def get_claim_and_stake_details(self, inputs):
        status = HTTPStatus.BAD_REQUEST
        try:
            schema = {
                "type": "object",
                "properties": {"address": {"type": "string"}, "airdrop_id": {"type": "string"}, "airdrop_window_id": {"type": "string"}},
                "required": ["address", "airdrop_id", "airdrop_window_id"],
            }

            validate(instance=inputs, schema=schema)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"]

            claimable_amount, wallet_address = AirdropRepository().get_airdrop_window_claimable_amount(
                airdrop_id, airdrop_window_id, address)
            stake_amount, is_stake_window_is_open, stake_window_start_time, stake_window_end_time = self.get_stake_window_details(
                airdrop_id, airdrop_window_id, address)
            stake_claim_details = AirdropStakeClaimDetails(
                airdrop_id, airdrop_window_id, claimable_amount, stake_amount, is_stake_window_is_open, stake_window_start_time, stake_window_end_time).to_dict()

            response = {"stake_claim_details": stake_claim_details}
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window History {e}")
            response = str(e)
        return status, response

    def get_stake_window_details(self, airdrop_id, airdrop_window_id, address):
        # TODO: Call the smart contract to get the details
        stake_amount = 0
        is_stake_window_is_open = False
        stake_window_start_time = 0
        stake_window_end_time = 0
        return stake_amount, is_stake_window_is_open, stake_window_start_time, stake_window_end_time

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
