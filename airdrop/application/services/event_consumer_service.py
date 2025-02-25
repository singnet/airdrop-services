import json
from datetime import datetime as dt
from http import HTTPStatus

import requests
from jsonschema import validate

from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.config import BlockFrostAccountDetails, DepositDetails, MIN_BLOCK_CONFIRMATION_REQUIRED
from airdrop.constants import AirdropClaimStatus, BlockFrostAPI, DEPOSIT_EVENT_TX_METADATA
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.claim_history_repo import ClaimHistoryRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.utils import Utils
from common.exceptions import ValidationFailedException
from common.logger import get_logger

user_registration_repo = UserRegistrationRepository()
utils = Utils()

logger = get_logger(__name__)


class EventConsumerService:
    def __init__(self, event):
        self.event = event

    @staticmethod
    def get_current_block_no():
        logger.info(f"Getting current block no")
        response = requests.get(BlockFrostAPI.get_last_block,
                                headers={"project_id": BlockFrostAccountDetails.project_id})
        if response.status_code == HTTPStatus.OK:
            return json.loads(response.text)["height"]
        raise Exception(f"Error in fetching current block no.\n"
                        f"Response from blockfrost API:\n"
                        f"Status: {response}"
                        f"Details: {response.text}")

    @staticmethod
    def get_transaction_details(transaction_hash):
        logger.info(f"Getting transaction details of transaction_hash={transaction_hash}")
        url = BlockFrostAPI.get_transaction_details.format(hash=transaction_hash)
        response = requests.get(url, headers={"project_id": BlockFrostAccountDetails.project_id})
        if response.status_code == HTTPStatus.OK:
            return json.loads(response.text)
        raise Exception(f"Error in getting transaction details.\n"
                        f"Response from blockfrost API:\n"
                        f"Status: {response}"
                        f"Details: {response.text}")

    def validate_block_confirmation(self, transaction_block_no):
        current_block_no = EventConsumerService.get_current_block_no()
        if current_block_no > (transaction_block_no + MIN_BLOCK_CONFIRMATION_REQUIRED):
            return None
        raise Exception(f"Block confirmation is not enough for event {self.event}")

    @staticmethod
    def get_stake_key_address(address):
        logger.info(f"Getting stake key for the address={address}")
        url = BlockFrostAPI.get_stake_address.format(address=address)
        response = requests.get(url, headers={"project_id": BlockFrostAccountDetails.project_id})
        if response.status_code == HTTPStatus.OK:
            return json.loads(response.text)["stake_address"]
        raise Exception(f"Error in fetching stake key address\n"
                        f"Response from blockfrost API:\n"
                        f"Status: {response}"
                        f"Details: {response.text}")

    @staticmethod
    def get_account_associated_addresses(stake_address):
        logger.info(f"Getting account associated addresses for the stake address={stake_address}")
        url = BlockFrostAPI.get_account_associated_addresses.format(stake_address=stake_address)
        response = requests.get(url, headers={"project_id": BlockFrostAccountDetails.project_id})
        if response.status_code == HTTPStatus.OK:
            associated_addresses = [record["address"] for record in json.loads(response.text)]
            return associated_addresses
        raise Exception(f"Error in fetching stake key address\n"
                        f"Response from blockfrost API:\n"
                        f"Status: {response}"
                        f"Details: {response.text}")


class DepositEventConsumerService(EventConsumerService):
    def validate_event_destination_address(self, deposit_address):
        if DepositDetails.address == deposit_address:
            return None
        raise ValidationFailedException(f"Deposit address validation failed for event {self.event}")

    def validate_token_details(self, tx_amount):
        if float(tx_amount) >= float(DepositDetails.amount_in_lovelace):
            return None
        raise ValidationFailedException(f"Token details validation failed for event {self.event}")

    def validate_user_input_addresses_for_unique_stake_address(self, input_addresses, stake_address):
        # In case of multiple input address, stake address should be same

        for address in input_addresses:
            stake_key = self.get_stake_key_address(address=address)
            if stake_key != stake_address:
                raise ValidationFailedException(
                    f"Multiple stake address for given input addresses for event {self.event}")

        return None

    def fetch_transaction_metadata(self, tx_metadata):
        try:
            json_metadata = tx_metadata[0]["json_metadata"]
            validate(instance=json_metadata, schema=DEPOSIT_EVENT_TX_METADATA)
        except Exception as e:
            logger.info(f"Metadata is not valid for event {self.event}.")
            return None

        return json_metadata

    def validate_deposit_event(self):
        """
            1. Validate block confirmations.
            2. Validate destination address.
            3. Validate token amount.
            4. Validate user input address for unique stake address.
            5. Fetch user ethereum address for given registration id.
            6. Validate user ethereum signature.
            7. Get claimable amount.
            7. Update claim history table.

        """
        message = json.loads(json.loads(self.event["Records"][0]["body"])["Message"])
        transaction_details = message["transaction_detail"]
        transaction_metadata = transaction_details.get("tx_metadata")

        tx_metadata = self.fetch_transaction_metadata(transaction_metadata)
        if not tx_metadata or tx_metadata is None:
            logger.info(f"Transaction metadata not available for the given event {json.dumps(self.event)} ")
            return

        v = tx_metadata["s3"]
        if v != '1c' and v != '1b':
            v = hex(int(v) + 27).replace('0x', '')

        ethereum_signature = tx_metadata["s1"] + tx_metadata["s2"] + v
        airdrop_window_id = tx_metadata["wid"]
        registration_id = tx_metadata["r1"] + tx_metadata["r2"]

        # Validate block confirmations.
        self.validate_block_confirmation(transaction_details["block_number"])

        # Validate destination address.
        self.validate_event_destination_address(message["address"])

        # Validate token amount.
        self.validate_token_details(transaction_details["tx_amount"])

        # Validate user cardano address.
        input_addresses = transaction_details["input_addresses"]
        first_input_address = input_addresses[0]
        stake_address_from_event = self.get_stake_key_address(first_input_address)

        if len(input_addresses) > 1:
            self.validate_user_input_addresses_for_unique_stake_address(input_addresses, stake_address_from_event)

        #  Fetch user ethereum address for given registration id
        user_registered, user_registration = user_registration_repo. \
            get_user_registration_details(registration_id=registration_id)
        if not user_registered:
            raise ValidationFailedException(f"Unable to find user for given registration_id in the event {self.event}")

        ethereum_address = user_registration.address
        cardano_address = user_registration.signature_details.get("message", {}).get("Airdrop", {}).get(
            "cardanoAddress", None)
        user_stake_address = self.get_stake_key_address(cardano_address)

        # Validate cardano address.
        if user_stake_address != stake_address_from_event:
            raise ValidationFailedException(f"Stake address mismatch.\nUser stake address {user_stake_address}."
                                            f"\nEvent stake address {stake_address_from_event}")

        # Validate ethereum eip 712 signature format
        ethereum_signature = utils.trim_prefix_from_string_message(prefix="0x", message=ethereum_signature)
        airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id)
        airdrop_id = airdrop_window.airdrop_id
        airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
        airdrop_class = AirdropServices().load_airdrop_class(airdrop)
        formatted_message = airdrop_class(airdrop_id, airdrop_window_id) \
            .format_user_claim_signature_message(registration_id)
        claim_sign_verified, recovered_address = utils.match_ethereum_signature(ethereum_address,
                                                                                formatted_message,
                                                                                ethereum_signature)
        if not claim_sign_verified:
            raise ValidationFailedException(f"Claim signature verification failed for event {self.event}")

        # Update transaction status for ADA deposited
        blockchain_method = "ada_transfer"
        ClaimHistoryRepository().update_claim_status(ethereum_address, airdrop_window_id, blockchain_method,
                                                     AirdropClaimStatus.ADA_RECEIVED.value)

        # Get claimable amount
        claimable_amount = AirdropRepository().fetch_total_rewards_amount(airdrop_id, ethereum_address)
        if claimable_amount == 0:
            raise Exception(f"Claimable amount is {claimable_amount} for event {self.event}")

        # Update claim history table
        claim_payload = {
            "airdrop_id": airdrop_id,
            "airdrop_window_id": airdrop_window_id,
            "address": ethereum_address,
            "blockchain_method": "token_transfer",
            "claimable_amount": claimable_amount,
            "unclaimed_amount": 0,
            "transaction_status": AirdropClaimStatus.PENDING.value,
            "claimed_on": dt.utcnow()
        }
        ClaimHistoryRepository().add_claim(claim_payload)
