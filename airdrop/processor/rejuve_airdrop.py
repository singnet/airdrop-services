import json
from typing import Dict, List, Tuple, Union

from web3 import Web3
from pycardano import Address

from airdrop.constants import AirdropClaimStatus, TransactionType
from airdrop.infrastructure.models import AirdropWindow, UserRegistration
from airdrop.application.types.windows import WindowRegistrationData
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.balance_snapshot import UserBalanceSnapshotRepository
from airdrop.infrastructure.repositories.claim_history_repo import ClaimHistoryRepository
from airdrop.infrastructure.repositories.pending_user_registration_repo import UserPendingRegistrationRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.utils import Utils, datetime_in_utcnow
from airdrop.config import RejuveAirdropConfig
from common.exceptions import ValidationFailedException
from common.logger import get_logger
from common.utils import (
    get_registration_receipt_cardano,
    get_registration_receipt_ethereum
)
from airdrop.constants import CARDANO_ADDRESS_PREFIXES, CardanoEra

logger = get_logger(__name__)


class RejuveAirdrop(DefaultAirdrop):

    def __init__(self, airdrop_id, airdrop_window_id=None):
        super().__init__(airdrop_id, airdrop_window_id)
        self.domain_name = "Rejuve Airdrop"
        self.register_all_window_at_once = False
        self.allow_update_registration = True
        self.is_claim_signature_required = True
        self.chain_context = {
            "deposit_address": RejuveAirdropConfig.deposit_address.value,
            "amount": RejuveAirdropConfig.pre_claim_transfer_amount.value["amount"],
            "chain": RejuveAirdropConfig.chain.value
        }
        self.claim_address = RejuveAirdropConfig.claim_address.value

    def check_user_eligibility(self, address: str) -> bool:
        if any(address.startswith(prefix) for prefix in CARDANO_ADDRESS_PREFIXES[CardanoEra.SHELLEY]):
            formatted_address = Address.from_primitive(address)

            if formatted_address.payment_part is not None and formatted_address.staking_part is not None:
                balances = UserBalanceSnapshotRepository().get_balances_by_staking_payment_parts_for_airdrop(
                    payment_part=str(formatted_address.payment_part),
                    staking_part=str(formatted_address.staking_part),
                    airdrop_id=self.id
                )

                return bool(balances and len(balances) > 0)

            logger.error(f"Staking and payment part not found for address: {address}")
            return False

        else:
            balances = UserBalanceSnapshotRepository().get_data_by_address(
                address=address,
                airdrop_id=self.id
            )

            return bool(balances and len(balances) > 0)

    def format_user_registration_signature_message(
        self,
        address: str,
        block_number: int,
        wallet_name: str,
    ) -> dict:
        formatted_message = {
            "airdropId": self.id,
            "airdropWindowId": self.window_id,
            "blockNumber": block_number,
            "walletAddress": address.lower(),
            "walletName": wallet_name
        }
        return formatted_message

    def format_trezor_user_registration_signature_message(
        self,
        block_number: int,
        wallet_name: str,
    ) -> dict:
        formatted_message = {
            "airdropId": self.id,
            "airdropWindowId": self.window_id,
            "blockNumber": block_number,
            "walletName": wallet_name
        }
        return formatted_message

    def format_and_get_claim_signature_details(self, **kwargs) -> tuple[list, list]:
        pass

    def match_signature(
        self,
        address: str,
        signature: str,
        block_number: int,
        wallet_name: str,
        key: str | None,
        reward_address: str | None = None,
    ) -> dict:
        network = Utils.recognize_blockchain_network(address)
        logger.info(f"Start of signature matching | address={address}, signature={signature}, network={network}")

        if network not in {"Ethereum", "Cardano"}:
            raise ValueError(f"Unsupported network: {network}")

        if network == "Ethereum":
            address = Web3.to_checksum_address(address)
        elif network == "Cardano" and key is None:
            raise ValueError("Key must be provided for Cardano signatures.")

        formatted_message = self.format_user_registration_signature_message(
            reward_address if reward_address else address,
            block_number=block_number,
            wallet_name=wallet_name
        )
        message = json.dumps(formatted_message, separators=(',', ':'))

        sign_verified = (
            Utils.match_ethereum_signature_eip191(address, message, signature)
            if network == "Ethereum"
            else Utils.match_cardano_signature(message, signature, key)
        )

        if not sign_verified:
            logger.error("Invalid signature")
            raise ValueError("Signature is not valid.")

        return formatted_message

    def generate_user_registration_receipt(
            self, airdrop_id: int,
            window_id: int,
            address: str
        ) -> str:
        # Get the unique receipt to be issued , users can use this receipt as evidence that
        # registration was done
        logger.info("Generate user registration receipt")
        secret_key = self.get_secret_key_for_receipt()
        network = Utils.recognize_blockchain_network(address)
        if network == "Ethereum":
            receipt = get_registration_receipt_ethereum(airdrop_id, window_id, address, secret_key)
        elif network == "Cardano":
            receipt = get_registration_receipt_cardano(airdrop_id, window_id, address, secret_key)
        return receipt

    def register(self, data: dict) -> list | str:
        logger.info(f"Starting the registration process for {self.__class__.__name__}")
        if "tx_hash" in data:
            return self.register_trezor(data)
        else:
            return self.register_regular_wallet(data)

    def register_regular_wallet(self, data: dict) -> list | str:
        logger.info("The process of registering regular wallets")
        address = data["address"]
        signature = data["signature"]
        block_number = data["block_number"]
        wallet_name = data["wallet_name"]
        key = data.get("key")

        if Utils.recognize_blockchain_network(address) == "Ethereum":
            address = Web3.to_checksum_address(address)

        registration_repo = UserRegistrationRepository()
        airdrop_window_repo = AirdropWindowRepository()
        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)

        formatted_message = self.match_signature(
            address=address,
            signature=signature,
            block_number=block_number,
            wallet_name=wallet_name,
            key=key,
        )

        is_registration_open = self.is_phase_window_open(
            airdrop_window.registration_start_period,
            airdrop_window.registration_end_period
        )
        if airdrop_window.registration_required and not is_registration_open:
            logger.error("Airdrop window is not accepting registration at this moment")
            raise Exception("Airdrop window is not accepting registration at this moment")

        is_user_eligible = self.check_user_eligibility(address=address)
        if not is_user_eligible:
            logger.error("Address is not eligible for this airdrop")
            raise Exception("Address is not eligible for this airdrop")

        is_registered, _ = registration_repo.get_user_registration_details(address, self.window_id)
        if is_registered:
            logger.error("Address is already registered for this airdrop window")
            raise Exception("Address is already registered for this airdrop window")

        receipt = self.generate_user_registration_receipt(self.id, self.window_id, address)
        registration_repo.register_user(
            self.window_id,
            address,
            receipt,
            formatted_message,
            block_number,
            signature
        )

        return receipt

    def register_trezor(self, data: dict) -> list | str:
        logger.info("The process of registering trezor wallets")
        address = Web3.to_checksum_address(data["address"])
        block_number = data["block_number"]
        wallet_name = data["wallet_name"]
        tx_hash = data["tx_hash"]

        registration_repo = UserRegistrationRepository()
        pending_registration_repo = UserPendingRegistrationRepository()
        airdrop_window_repo = AirdropWindowRepository()
        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)

        is_registration_open = self.is_phase_window_open(
            airdrop_window.registration_start_period,
            airdrop_window.registration_end_period
        )

        if airdrop_window.registration_required and not is_registration_open:
            logger.error("Airdrop window is not accepting registration at this moment")
            raise Exception("Airdrop window is not accepting registration at this moment")

        is_user_eligible = self.check_user_eligibility(address=address)
        if not is_user_eligible:
            logger.error("Address is not eligible for this airdrop")
            raise Exception("Address is not eligible for this airdrop")

        is_registered, _ = registration_repo.get_user_registration_details(address, self.window_id)
        if is_registered:
            logger.error("Address is already registered for this airdrop window")
            raise Exception("Address is already registered for this airdrop window")

        is_pending_registered = pending_registration_repo.is_pending_user_registration_exist(address, self.window_id)
        if is_pending_registered:
            logger.error("Address is already waiting to be registered for this airdrop window")
            raise Exception("Address is already waiting to be registered for this airdrop window")

        formatted_message = self.format_trezor_user_registration_signature_message(
            block_number=block_number,
            wallet_name=wallet_name
        )

        receipt = self.generate_user_registration_receipt(self.id, self.window_id, address)
        pending_registration_repo.register_user(
            airdrop_window_id=self.window_id,
            address=address,
            receipt=receipt,
            tx_hash=tx_hash,
            signature_details=formatted_message,
            block_number=block_number,
            transaction_type=TransactionType.REGISTRATION.value
        )

        return receipt

    def update_registration(self, data: dict):
        """
        Update the user's registration details for a specific airdrop window.

        Steps:
        1. Validate the airdrop window exists.
        2. Check if claim phase is open.
        3. Check if the user is eligible for the airdrop.
        4. Match the provided signature to confirm identity.
        5. Ensure the user is already registered.
        6. Generate new receipt.
        7. Update the registration with new signature details.
        """
        logger.info(f"Starting registration update process for {self.__class__.__name__}")

        address = data["address"]
        signature = data["signature"]
        reward_address = data["reward_address"]
        block_number = data["block_number"]
        wallet_name = data["wallet_name"]
        key = data.get("key")

        registration_repo = UserRegistrationRepository()
        airdrop_window_repo = AirdropWindowRepository()

        if Utils.recognize_blockchain_network(address) == "Ethereum":
            address = Web3.to_checksum_address(address)

        airdrop_window: AirdropWindow = airdrop_window_repo.get_airdrop_window_by_id(self.window_id)
        if not airdrop_window:
            raise Exception(f"Airdrop window does not exist: {self.window_id}")

        if not self.is_phase_window_open(
            airdrop_window.claim_start_period,
            airdrop_window.claim_end_period
        ):
            raise Exception("Airdrop window is not accepting claim at this moment")

        if not self.check_user_eligibility(address=address):
            logger.error(f"Address {address} is not eligible for airdrop in window {self.window_id}")
            raise Exception("Address is not eligible for this airdrop.")

        signature_details = self.match_signature(
            address=address,
            signature=signature,
            block_number=block_number,
            wallet_name=wallet_name,
            key=key,
            reward_address=reward_address
        )

        is_registered, _ = registration_repo.get_user_registration_details(address, self.window_id)
        if not is_registered:
            logger.error(f"Address {address} is not registered for window {self.window_id}")
            raise Exception("Address is not registered for this airdrop window.")

        receipt = self.generate_user_registration_receipt(self.id, self.window_id, reward_address)

        registration_repo.update_registration(
            airdrop_window_id=self.window_id,
            address=address,
            signature_details=signature_details,
            receipt=receipt
        )

        claimable_amount, total_eligible_amount = self.get_claimable_amount(user_address=address)

        return {
            "airdrop_id": str(self.id),
            "airdrop_window_id": str(airdrop_window.id),
            "claimable_amount": str(claimable_amount),
            "total_eligibility_amount": str(total_eligible_amount),
            "chain_context": self.chain_context,
            "registration_id": receipt
        }

    def generate_multiple_windows_eligibility_response(
        self,
        is_user_eligible: bool,
        airdrop_id: int,
        address: str,
        windows_registration_data: List[WindowRegistrationData],
        rewards_awarded: int,
        with_signature: bool,
    ) -> dict:
        claimable_amount, _ = self.get_claimable_amount(address)

        response = {
            "is_eligible": is_user_eligible,
            "is_claimable": claimable_amount > 0,
            "windows": {}
        }

        if with_signature:
            response.update({
                "airdrop_window_rewards": rewards_awarded,
                "user_address": address,
                "airdrop_id": airdrop_id,
            })

        for window_data in windows_registration_data:
            window_info: Dict[str, Union[str, dict, None]] = {
                "claim_status": window_data.claim_status.value
            }

            if with_signature:
                registration_details = {}
                if window_data.registration_details:
                    rd = window_data.registration_details
                    registration_details = {
                        "registration_id": rd.registration_id,
                        "reject_reason": rd.reject_reason,
                        "registered_at": str(rd.registered_at),
                    }

                window_info["airdrop_window_claim_status"] = window_data.airdrop_window_claim_status.value \
                    if window_data.airdrop_window_claim_status else None
                window_info["registration_details"] = registration_details

            response["windows"][window_data.window_id] = window_info

        return response

    def generate_eligibility_response(
        self,
        airdrop_id: int,
        airdrop_window_id: int,
        address: str,
        is_user_eligible: bool,
        is_registered: bool,
        user_registration: UserRegistration,
        is_airdrop_window_claimed: bool,
        airdrop_claim_status: AirdropClaimStatus,
        rewards_awarded: int,
        is_claimable: bool
    ) -> dict:
        registration_id, reject_reason, registration_details = "", None, dict()

        if is_registered:
            registration_id = user_registration.receipt_generated
            reject_reason = user_registration.reject_reason
            registration_details = {
                "registration_id": user_registration.receipt_generated,
                "reject_reason": user_registration.reject_reason,
                "registered_at": str(user_registration.registered_at),
            }
        response = {
            "is_eligible": is_user_eligible,
            "is_already_registered": is_registered,
            "is_airdrop_window_claimed": is_airdrop_window_claimed,
            "airdrop_window_claim_status": airdrop_claim_status,
            "user_address": address,
            "airdrop_id": airdrop_id,
            "airdrop_window_id": airdrop_window_id,
            "reject_reason": reject_reason,
            "airdrop_window_rewards": rewards_awarded,
            "registration_id": registration_id,
            "is_claimable": is_claimable,
            "registration_details": registration_details
        }

        return response

    def get_claimable_amount(self, user_address: str) -> Tuple[int, int]:
        airdrop_window_repo = AirdropRepository()
        claimable_amount = airdrop_window_repo.fetch_total_rewards_amount(self.id, user_address, airdrop_class="RejuveAirdrop")
        total_eligible_amount = airdrop_window_repo.fetch_total_eligibility_amount(self.id, user_address)

        return claimable_amount, total_eligible_amount

    def validate_deposit_event(
        self,
        request_message: dict,
        signature: str,
        transaction_details: dict,
        registration_id: str,
        user_registration: UserRegistration,
    ):
        logger.info(
            "Validating deposit event for Rejuve Airdrop"
            f" {self.id} and window {self.window_id}"
            f" registration_id: {registration_id}"
            f" transaction_details: {transaction_details}"
            f" user_registration: {user_registration}"
        )

        input_addresses = transaction_details["input_addresses"]
        first_input_address = input_addresses[0]
        stake_address_from_event = Utils.get_stake_key_address(first_input_address)

        reward_address = user_registration.signature_details.get("walletAddress")
        registration_address = str(user_registration.address)

        if reward_address is None:
            raise Exception("Error in parsing signature details:", user_registration.signature_details)

        reward_stake_address = Utils.get_stake_key_address(reward_address)

        # Validate cardano address.
        if reward_stake_address != stake_address_from_event:
            raise ValidationFailedException(
                f"Stake address mismatch.\nReward stake address {reward_stake_address}."
                f"\nEvent stake address {stake_address_from_event}"
            )

        if signature is not None:
            registration_address = Web3.to_checksum_address(registration_address)
            signature = Utils.trim_prefix_from_string_message(prefix="0x", message=signature)

            formatted_message = self.format_user_claim_signature_message(registration_id)
            message = json.dumps(formatted_message, separators=(',', ':'))

            if not Utils.match_ethereum_signature_eip191(
                registration_address,
                message,
                signature
            ):
                logger.error(
                    "Claim signature verification failed \n"
                    f"address = {registration_address} \n"
                    f"message = {message} \n"
                    f"signature = {signature} \n"
                )
                raise ValidationFailedException(f"Claim signature verification failed for {registration_id}")

        # Check for a transaction with the PENDING status, if not, create it
        blockchain_method = "ada_transfer"
        tx_amount = transaction_details["tx_amount"]
        amount = float(tx_amount) / (10 ** int(tx_amount.split('E')[1]))
        ClaimHistoryRepository().create_transaction_if_not_found(
            address=registration_address,
            airdrop_id=self.id,
            window_id=self.window_id,
            tx_hash=request_message["tx_hash"],
            amount=amount,
            blockchain_method=blockchain_method
        )

        # Update transaction status for ADA deposited
        ClaimHistoryRepository().update_claim_status(
            registration_address,
            self.window_id,
            blockchain_method,
            AirdropClaimStatus.ADA_RECEIVED.value
        )

        # Get claimable amount
        claimable_amount = AirdropRepository().fetch_total_rewards_amount(self.id, registration_address, "RejuveAirdrop")
        if claimable_amount == 0:
            raise Exception(f"Claimable amount is {claimable_amount} for event")

        # Update claim history table
        claim_payload = {
            "airdrop_id": self.id,
            "airdrop_window_id": self.window_id,
            "address": user_registration.address,
            "blockchain_method": "token_transfer",
            "claimable_amount": claimable_amount,
            "unclaimed_amount": 0,
            "transaction_status": AirdropClaimStatus.PENDING.value,
            "claimed_on": datetime_in_utcnow()
        }
        ClaimHistoryRepository().add_claim(claim_payload)

    def format_user_claim_signature_message(self, registration_id: str) -> dict:
        formatted_message = {
            "airdropWindowId": int(self.window_id),
            "registrationId": registration_id,
        }

        return formatted_message
