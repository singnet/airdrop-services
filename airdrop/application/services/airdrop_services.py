import ast
from datetime import datetime
from http import HTTPStatus
from pydoc import locate
from typing import Type

import web3
from eth_account.messages import encode_defunct
from jsonschema import validate, ValidationError
from web3 import Web3, types

from airdrop.config import NETWORK, DEFAULT_REGION
from airdrop.config import (
    SIGNER_PRIVATE_KEY,
    SIGNER_PRIVATE_KEY_STORAGE_REGION,
    NUNET_SIGNER_PRIVATE_KEY_STORAGE_REGION,
    NUNET_SIGNER_PRIVATE_KEY,
    SLACK_HOOK
)
from airdrop.constants import (
    STAKING_CONTRACT_PATH,
    CLAIM_SCHEMA,
    AirdropEvents,
    AirdropClaimStatus,
    PROCESSOR_PATH,
    Blockchain
)
from airdrop.domain.factory.airdrop_factory import AirdropFactory
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.processor.default_airdrop import DefaultAirdrop, BaseAirdrop
from airdrop.utils import Utils as ut
from common.boto_utils import BotoUtils
from common.logger import get_logger
from common.utils import (
    generate_claim_signature,
    generate_claim_signature_with_total_eligibile_amount,
    get_contract_instance,
    get_transaction_receipt_from_blockchain,
    get_checksum_address,
    Utils
)

logger = get_logger(__name__)


class AirdropServices:

    def airdrop_txn_watcher(self):

        pending_txns = AirdropRepository().get_pending_txns()
        logger.info(f"pending_txns {len(pending_txns)}")

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
                    if txn_hash_from_receipt.lower() == txn_hash.lower():
                        AirdropRepository().update_txn_status(txn_hash_from_receipt, txn_receipt_status)
                    else:
                        AirdropRepository().airdrop_window_claim_txn(
                            airdrop_id=txn.airdrop_id,
                            airdrop_window_id=txn.airdrop_window_id,
                            address=txn.address,
                            txn_hash=txn_hash_from_receipt,
                            amount=txn.claimable_amount
                        )
                        logger.warning(f"Transaction hash mismatch {txn_hash_from_receipt} {txn_hash}, "
                                       "creating new entry")

            except BaseException as e:
                print(f"Exception on Airdrop Txn Watcher {e}")

    def get_txn_receipt(self, txn_hash: str) -> types.TxReceipt:
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
            amount = event_payload['amount'] or event_payload['airDropAmount']
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
        logger.info("Calling the window stake details receiving function")
        status = HTTPStatus.BAD_REQUEST
        try:
            schema = {
                "type": "object",
                "properties": {"address": {"type": "string"}, "airdrop_id": {"type": "string"},
                               "airdrop_window_id": {"type": "string"}},
                "required": ["address", "airdrop_id", "airdrop_window_id"],
            }

            validate(instance=inputs, schema=schema)

            user_address = inputs["address"]
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]

            user_wallet_address = get_checksum_address(user_address)

            airdrop_rewards, user_address, contract_address, token_address, staking_contract_address, \
            total_eligibility_amount = AirdropRepository().get_airdrop_window_claimable_info(
                airdrop_id, airdrop_window_id, user_wallet_address)

            staking_contract_address, token_name = AirdropRepository(
            ).get_staking_contract_address(airdrop_id)

            is_stakable, stakable_amount, tranfer_to_wallet = self.get_stake_info(
                staking_contract_address, user_wallet_address, int(airdrop_rewards), int(airdrop_window_id))
            stakable_tokens = stakable_amount

            stake_details = AirdropFactory.convert_stake_claim_details_to_model(
                airdrop_id, airdrop_window_id, user_wallet_address, tranfer_to_wallet, stakable_tokens, is_stakable,
                token_name, airdrop_rewards, total_eligibility_amount)

            response = {"stake_details": stake_details}
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window History {e}")
            response = str(e)

        return status, response

    def get_stake_info(self, contract_address, user_wallet_address, airdrop_rewards, airdrop_window_id):
        try:

            is_stake_window_is_open, max_stake_amount, max_window_stake_amount, total_window_amount_staked \
                = self.get_stake_window_details(
                contract_address)

            is_user_can_stake, already_staked_amount = self.get_stake_details_of_address(
                contract_address, user_wallet_address)

            is_stakable, stake_amount, transfer_to_wallet = self.get_stake_and_claimable_amounts(
                airdrop_rewards, is_stake_window_is_open, max_stake_amount, already_staked_amount,
                max_window_stake_amount, total_window_amount_staked, airdrop_window_id)
            return is_stakable, stake_amount, transfer_to_wallet

        except BaseException as e:
            logger.error(e)
            Utils().report_slack(
                type=0, slack_message=f"Issue with Stake window Opened exeption {e} user_address {user_wallet_address},"
                                      f" stake_contract_address: {contract_address}", slack_config=SLACK_HOOK
            )
            return False, 0, airdrop_rewards

    def get_stake_and_claimable_amounts(self, airdrop_rewards, is_stake_window_is_open, max_stake_amount,
                                        already_staked_amount, max_window_stake_amount, total_window_amount_staked,
                                        airdrop_window_id):

        transfer_to_wallet = airdrop_rewards
        stakable_amount = 0
        airdrop_window_details = AirdropRepository().get_airdrop_window_details(airdrop_window_id)
        minimum_stake_amount = airdrop_window_details.minimum_stake_amount
        # User can stake if stake window is open and user can stake
        if is_stake_window_is_open:
            # get the limit per user
            user_stake_limit = max_stake_amount - already_staked_amount
            # get the limit per window for staking
            window_stake_limit = max_window_stake_amount - total_window_amount_staked

            if user_stake_limit < 0 or window_stake_limit < 0:
                # Ideally this should never happen, however if it does, Stake should be disabled
                raise Exception(f"Issue with Stake window Opened, user_stake_limit{user_stake_limit},"
                                f" window_stake_limit: {window_stake_limit}")

            # take the minimum of the two on the max amount that a user can stake !
            allowed_amount_for_stake = min(user_stake_limit, window_stake_limit)

            if airdrop_rewards <= allowed_amount_for_stake:
                # If airdrop rewards is less than allowed amount for stake then stake the full airdrop rewards
                stakable_amount = airdrop_rewards
            else:
                stakable_amount = allowed_amount_for_stake

            # Ensure the stake amount is greater than minimum stake amount
            if minimum_stake_amount > stakable_amount:
                stakable_amount = 0
            # Amount user can claim to wallet after staking
            if stakable_amount > 0:
                transfer_to_wallet = airdrop_rewards - stakable_amount

        is_stakable = True if stakable_amount > 0 else False

        return is_stakable, stakable_amount, transfer_to_wallet

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
            logger.info("stake_submission_start_period", stake_submission_start_period)

            stake_submission_end_period = int(stakemap[1])
            logger.info("stake_submission_end_period", stake_submission_end_period)

            # get the maximum amount of stake that is allowed for a given user
            max_stakable_amount = stakemap[3]
            logger.info("max_stakable_amount", max_stakable_amount)

            # get the maximum amount of stake that is allowed in a given window across all users
            max_window_amount = stakemap[5]
            logger.info("max_window_amount", max_window_amount)

            now = datetime.now()
            logger.info("Stake window details retrieved")
            # get the amount staked so far in this window across all users
            total_window_amount_staked = contract.functions.windowTotalStake().call()

            # Check if stake window is open or not if stake start & end period is in between current time
            is_stake_window_open = datetime.fromtimestamp(
                stake_submission_end_period) >= now >= datetime.fromtimestamp(stake_submission_start_period)
            logger.info("is_stake_window_open", is_stake_window_open)
            return is_stake_window_open, max_stakable_amount, max_window_amount, total_window_amount_staked
        except BaseException as e:
            logger.error(e)
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
                "properties": {"address": {"type": "string"}, "airdrop_id": {"type": "string"},
                               "airdrop_window_id": {"type": "string"}, "txn_hash": {"type": "string"},
                               "amount": {"type": "string"}, "blockchain_method": {"type": "string"}},
                "required": ["address", "airdrop_id", "airdrop_window_id", "txn_hash", "amount", "blockchain_method"],
            }

            validate(instance=inputs, schema=schema)

            user_address = inputs["address"]
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            txn_hash = inputs["txn_hash"]
            amount = inputs["amount"]
            blockchain_method = inputs["blockchain_method"]

            if ut.recognize_blockchain_network(user_address) == Blockchain.ETHEREUM.value:
                user_address = Web3.to_checksum_address(user_address)

            AirdropRepository().airdrop_window_claim_txn(
                airdrop_id, airdrop_window_id, user_address, txn_hash, amount, blockchain_method)

            logger.info(f"Transaction with {blockchain_method = }, {user_address = }, "
                        f"{airdrop_id = }, {airdrop_window_id = }, {txn_hash = } "
                        f"added to claim_history table")

            response = HTTPStatus.OK.phrase
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
            logger.exception(f"ValidationError on Airdrop Window Claim {str(e)}")
        except BaseException as e:
            logger.exception(f"BaseException on Airdrop Window Claim {str(e)}")
            response = str(e)

        return status, response

    def airdrop_window_claim(self, inputs):
        status = HTTPStatus.BAD_REQUEST
        try:
            validate(instance=inputs, schema=CLAIM_SCHEMA)

            user_address = inputs["address"]
            airdrop_id = int(inputs["airdrop_id"])
            airdrop_window_id = int(inputs["airdrop_window_id"])

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if airdrop is None:
                raise Exception("Airdrop id is not valid.")

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id)
            if airdrop_window is None:
                raise Exception("Airdrop window id is not valid.")

            airdrop_class = self.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            claimable_amount, total_eligible_amount = airdrop_object.get_claimable_amount(user_address=user_address)

            if airdrop_object.is_claim_signature_required:
                claim_signature_private_key = self.get_private_key_for_generating_claim_signature(
                    secret_name=airdrop_object.claim_signature_private_key_secret)
                signature_parameters = {
                    "claimable_amount": claimable_amount,
                    "total_eligible_amount": total_eligible_amount,
                    "user_address": user_address,
                    "contract_address": airdrop.contract_address,
                    "token_address": airdrop.token_address
                }
                signature_format, formatted_message = airdrop_object.format_and_get_claim_signature_details(
                    signature_parameters=signature_parameters
                )
                signature = self.generate_signature(claim_signature_private_key, signature_format, formatted_message)
            else:
                signature = "Not Applicable."

            response = {
                "airdrop_id": str(airdrop.id),
                "airdrop_window_id": str(airdrop_window.id),
                "user_address": user_address,
                "signature": signature,
                "claimable_amount": str(claimable_amount),
                "token_address": airdrop.token_address,
                "contract_address": airdrop.contract_address,
                "staking_contract_address": airdrop.staking_contract_address,
                "total_eligibility_amount": str(total_eligible_amount),
                "chain_context": airdrop_object.chain_context
            }

            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window Claim {e}")
            response = str(e)

        return status, response

    # this method is used only for Nunet OCCAM contract, once the claim window closes for Nunet OCCAM , we will
    # delete this method airdrop_window_claims
    def occam_airdrop_window_claim(self, inputs):
        status = HTTPStatus.BAD_REQUEST
        try:

            validate(instance=inputs, schema=CLAIM_SCHEMA)

            user_address = inputs["address"]
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]

            airdrop_repo = AirdropRepository()
            airdrop_repo.is_claimed_airdrop_window(user_address, airdrop_window_id)

            claimable_amount, user_wallet_address, contract_address, token_address, staking_contract_address, total_eligibility_amount = AirdropRepository().get_airdrop_window_claimable_info(
                airdrop_id, airdrop_window_id, user_address)

            signature = self.get_signature_for_airdrop_window_id(
                claimable_amount, airdrop_id, airdrop_window_id, user_wallet_address, contract_address, token_address)

            response = {
                "airdrop_id": airdrop_id,
                "airdrop_window_id": airdrop_window_id,
                "user_address": user_address,
                "signature": signature,
                "claimable_amount": str(claimable_amount),
                "token_address": token_address,
                "contract_address": contract_address,
                "staking_contract_address": staking_contract_address,
                "total_eligibility_amount": str(total_eligibility_amount)
            }

            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            print(f"Exception on Airdrop Window Claim {e}")
            response = str(e)

        return status, response

    def get_signature_for_airdrop_window_id(self, amount, airdrop_id, airdrop_window_id, user_wallet_address,
                                            contract_address, token_address):
        try:

            boto_client = BotoUtils(
                region_name=SIGNER_PRIVATE_KEY_STORAGE_REGION)
            private_key = boto_client.get_parameter_value_from_secrets_manager(
                secret_name=SIGNER_PRIVATE_KEY)

            return generate_claim_signature(
                amount, airdrop_id, airdrop_window_id, user_wallet_address, contract_address, token_address,
                private_key)

        except BaseException as e:
            raise e

    def get_signature_for_airdrop_window_id_with_totaleligibilty_amount(self, amount, total_eligible_amount, airdrop_id,
                                                                        airdrop_window_id, user_wallet_address,
                                                                        contract_address, token_address):
        try:
            boto_client = BotoUtils(
                region_name=NUNET_SIGNER_PRIVATE_KEY_STORAGE_REGION)
            private_key = boto_client.get_parameter_value_from_secrets_manager(
                secret_name=NUNET_SIGNER_PRIVATE_KEY)

            return generate_claim_signature_with_total_eligibile_amount(
                total_eligible_amount, amount, airdrop_id, airdrop_window_id, user_wallet_address, contract_address,
                token_address, private_key)

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
            status = HTTPStatus.INTERNAL_SERVER_ERROR
        return status, response

    @staticmethod
    def generate_signature(private_key, data_types: list, values: list):
        message = Web3.solidity_keccak(data_types, values)
        message_hash = encode_defunct(message)
        web3_object = Web3(web3.providers.HTTPProvider(NETWORK["http_provider"]))
        signed_message = web3_object.eth.account.sign_message(message_hash, private_key=private_key)

        return signed_message.signature.hex()

    @staticmethod
    def get_private_key_for_generating_claim_signature(secret_name):
        boto_client = BotoUtils(region_name=DEFAULT_REGION)
        try:
            return boto_client.get_parameter_value_from_secrets_manager(secret_name=secret_name)
        except Exception as e:
            raise Exception("Unable to fetch private key for generating claim signature.")

    @staticmethod
    def load_airdrop_class(airdrop) -> Type[BaseAirdrop]:
        if airdrop.airdrop_processor:
            airdrop_class = locate(f"{PROCESSOR_PATH}.{airdrop.airdrop_processor}")
            if not isinstance(airdrop_class, type):
                raise TypeError(f"Located object {airdrop_class} is not a class.")
            if not issubclass(airdrop_class, BaseAirdrop):
                raise TypeError(f"{airdrop_class} is not a subclass of BaseAirdrop")
        else:
            airdrop_class = DefaultAirdrop
        return airdrop_class
