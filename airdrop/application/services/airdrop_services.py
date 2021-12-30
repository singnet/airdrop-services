import ast
from datetime import datetime

from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from jsonschema import validate, ValidationError
from http import HTTPStatus
from common.boto_utils import BotoUtils
from common.utils import generate_claim_signature, get_contract_instance, get_transaction_receipt_from_blockchain, get_checksum_address
from airdrop.config import SIGNER_PRIVATE_KEY, SIGNER_PRIVATE_KEY_STORAGE_REGION, MAX_STAKE_LIMIT
from airdrop.constants import STAKING_CONTRACT_PATH, AirdropEvents, AirdropClaimStatus
from airdrop.domain.factory.airdrop_factory import AirdropFactory
from airdrop.domain.models.airdrop_claim import AirdropClaim


class AirdropServices:

    def airdrop_txn_watcher(self):

        pending_txns = AirdropRepository().get_pending_txns()

        for txn in pending_txns:
            try:
                txn_hash = txn.transaction_hash
                receipt = self.get_txn_receipt(txn_hash)
                if receipt is not None:
                    print(f"Receipt for txn {txn_hash} is {str(receipt)}")
                    txn_hash_from_receipt = receipt.transactionHash.hex()
                    if receipt.status == 1:
                        txn_receipt_status = AirdropClaimStatus.SUCCESS.value
                    else:
                        txn_receipt_status = AirdropClaimStatus.FAILED.value
                    if(txn_hash_from_receipt.lower() == txn_hash.lower()):
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

    def airdrop_event_consumer(self, event):
        response = {}
        status = HTTPStatus.BAD_REQUEST

        event_data = event['data']
        event_name = event_data['event']

        if event_name == AirdropEvents.AIRDROP_CLAIM.value:
            self.update_airdrop_window_claim_status(event_data)
            status = HTTPStatus.OK
        else:
            response = "Unsupported event"

        return status, response

    def update_airdrop_window_claim_status(self, event):
        try:
            event_payload = ast.literal_eval(event["json_str"])
            user_address = event_payload['claimer']
            amount = event_payload['amount']
            airdrop_id = event_payload['airDropId']
            airdrop_window_id = event_payload['airDropWindowId']
            txn_hash = event['transactionHash']
            txn_status = AirdropClaimStatus.SUCCESS.value
            AirdropRepository().create_or_update_txn(
                airdrop_id, airdrop_window_id, user_address, txn_hash, txn_status, amount)
            return True
        except BaseException as e:
            print(f"Exception on Airdrop claim status update {e}")
            return False

    def get_airdrop_window_stake_details(self, inputs):
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
            airdrop_window_id = inputs["airdrop_id"]

            address = get_checksum_address(user_address)

            rewards, user_address, contract_address, token_address, staking_contract_address = AirdropRepository().get_airdrop_window_claimable_info(
                airdrop_id, airdrop_window_id, address)

            staking_contract_address, stakable_token_name = AirdropRepository(
            ).get_staking_contract_address(airdrop_id)

            is_stakable, stakable_amount, tranfer_to_wallet = self.get_stake_info(
                staking_contract_address, address, int(rewards))
            stakable_tokens = stakable_amount

            stake_details = AirdropFactory.convert_stake_claim_details_to_model(
                airdrop_id, airdrop_window_id, address, tranfer_to_wallet, stakable_tokens, is_stakable, stakable_token_name)

            response = {"stake_details": stake_details}
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window History {e}")
            response = str(e)

        return status, response

    def get_stake_info(self, contract_address, address, airdrop_rewards):
        try:

            is_stake_window_is_open, max_stake_amount = self.get_stake_window_details(
                contract_address)

            is_user_can_stake, already_staked_amount = self.get_stake_details_of_address(
                contract_address, address)

            is_stakable, stakable_amount, tranfer_to_wallet = self.get_stake_and_claimable_amounts(
                airdrop_rewards, is_stake_window_is_open, max_stake_amount, is_user_can_stake, already_staked_amount)

            return is_stakable, stakable_amount, tranfer_to_wallet
        except BaseException as e:
            raise e("Exception on get_stake_info {}".format(e))

    def get_stake_and_claimable_amounts(self, airdrop_rewards, is_stake_window_is_open, max_stake_amount, is_user_can_stake, already_staked_amount):
        # User can stake if stake window is open and user can stake
        is_stakable = True if is_user_can_stake and is_stake_window_is_open else False

        allowed_amount_for_stake = max_stake_amount - already_staked_amount

        if(airdrop_rewards <= allowed_amount_for_stake):
            # If airdrop rewards is less than allowed amount for stake then stake the full airdrop rewards
            stakable_amount = airdrop_rewards
        else:
            stakable_amount = allowed_amount_for_stake

        # Amount user can claim to wallet after staking
        tranfer_to_wallet = airdrop_rewards - stakable_amount

        return is_stakable, stakable_amount, tranfer_to_wallet

    def get_stake_details_of_address(self, contract_address, user_wallet):
        try:
            contract = get_contract_instance(
                STAKING_CONTRACT_PATH, contract_address, contract_name='STAKING')

            stake_info = contract.functions.getStakeInfo(user_wallet).call()
            is_user_can_stake = stake_info[0]
            already_staked_amount = stake_info[1]

            return is_user_can_stake, already_staked_amount
        except BaseException as e:
            raise e("Exception on get_stake_details_of_address {}".format(e))

    def get_stake_window_details(self, staking_contract_address):
        try:
            contract = get_contract_instance(
                STAKING_CONTRACT_PATH, staking_contract_address, contract_name='STAKING')

            current_stakemap_index = contract.functions.currentStakeMapIndex().call()
            stakemap = contract.functions.stakeMap(
                current_stakemap_index).call()

            stake_submission_start_period = int(stakemap[0])
            stake_submission_end_period = int(stakemap[1])
            max_stakable_amount = stakemap[3]
            now = datetime.now()

            # Check if stake window is open or not if stake start & end period is in between current time
            is_stake_window_open = now <= datetime.fromtimestamp(
                stake_submission_end_period) and now >= datetime.fromtimestamp(stake_submission_start_period)

            return is_stake_window_open, max_stakable_amount
        except BaseException as e:
            raise e("Exception on get_stake_window_info {}".format(e))

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
                "properties": {"address": {"type": "string"}, "airdrop_id": {"type": "string"}, "airdrop_window_id": {"type": "string"}, "txn_hash": {"type": "string"}, "amount": {"type": "string"}, "blockchain_method": {"type": "string"}},
                "required": ["address", "airdrop_id", "airdrop_window_id", "txn_hash", "amount", "blockchain_method"],
            }

            validate(instance=inputs, schema=schema)

            user_address = inputs["address"]
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            txn_hash = inputs["txn_hash"]
            amount = inputs["amount"]
            blockchain_method = inputs["blockchain_method"]

            AirdropRepository().airdrop_window_claim_txn(
                airdrop_id, airdrop_window_id, user_address, txn_hash, amount, blockchain_method)

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

            claimable_amount, user_wallet_address, contract_address, token_address, staking_contract_address = AirdropRepository().get_airdrop_window_claimable_info(
                airdrop_id, airdrop_window_id, user_address)

            signature = self.get_signature_for_airdrop_window_id(
                claimable_amount, airdrop_id, airdrop_window_id, user_wallet_address, contract_address, token_address)

            response = AirdropClaim(airdrop_id,
                                    airdrop_window_id, user_wallet_address, signature, claimable_amount, token_address, contract_address, staking_contract_address).to_dict()

            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window Claim {e}")
            response = str(e)

        return status, response

    def get_signature_for_airdrop_window_id(self, amount, airdrop_id, airdrop_window_id, user_wallet_address, contract_address, token_address):
        try:

            boto_client = BotoUtils(
                region_name=SIGNER_PRIVATE_KEY_STORAGE_REGION)
            private_key = boto_client.get_parameter_value_from_secrets_manager(
                secret_name=SIGNER_PRIVATE_KEY)

            return generate_claim_signature(
                amount, airdrop_id, airdrop_window_id, user_wallet_address, contract_address, token_address, private_key)

        except BaseException as e:
            raise e

    def get_airdrops_schedule(self, airdrop_id):
        status = HTTPStatus.BAD_REQUEST

        try:
            response = AirdropRepository().get_airdrops_schedule(airdrop_id)
            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response
