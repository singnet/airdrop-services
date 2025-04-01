from datetime import datetime
from http import HTTPStatus
from typing import List

from jsonschema import validate, ValidationError

from blockfrost import BlockFrostApi
from blockfrost.utils import ApiError as BlockFrostApiError
from web3 import Web3

from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.config import BlockFrostAPIBaseURL, BlockFrostAccountDetails
from airdrop.constants import (
    ELIGIBILITY_SCHEMA,
    ADDRESS_ELIGIBILITY_SCHEMA,
    USER_REGISTRATION_SCHEMA,
    AirdropClaimStatus,
    UserClaimStatus
)
from airdrop.application.types.windows import WindowRegistrationData, RegistrationDetails
from airdrop.infrastructure.models import PendingTransaction
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.pending_transaction_repo import PendingTransactionRepository
from airdrop.infrastructure.repositories.claim_history_repo import ClaimHistoryRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.utils import Utils, datetime_in_utcnow
from common.exceptions import BadRequestException, TransactionNotFound
from common.logger import get_logger

logger = get_logger(__name__)


class UserRegistrationServices:

    @staticmethod
    def __generate_user_claim_status(
        is_registered: bool,
        airdrop_claim_status: AirdropClaimStatus | None,
    ) -> UserClaimStatus:
        logger.debug(
            f"Generate user claim status"
            f"is_registered = {is_registered}, status = {airdrop_claim_status}"
        )
        if not is_registered:
            return UserClaimStatus.NOT_REGISTERED
        elif airdrop_claim_status == AirdropClaimStatus.SUCCESS:
            return UserClaimStatus.RECEIVED
        elif airdrop_claim_status in (
            AirdropClaimStatus.PENDING,
            AirdropClaimStatus.ADA_RECEIVED,
            AirdropClaimStatus.CLAIM_INITIATED,
            AirdropClaimStatus.CLAIM_SUBMITTED
        ):
            return UserClaimStatus.PENDING
        elif airdrop_claim_status == AirdropClaimStatus.NOT_STARTED:
            return UserClaimStatus.NOT_STARTED
        elif airdrop_claim_status in (
            AirdropClaimStatus.FAILED,
            None
        ):
            return UserClaimStatus.READY_TO_CLAIM
        else:
            logger.error(f"Unexpected aidrop_claim_status: {airdrop_claim_status}")
            raise Exception(f"Unexpected aidrop_claim_status: {airdrop_claim_status}")

    @staticmethod
    def __get_registration_data(address: str, airdrop_window_id: int) -> WindowRegistrationData:
        is_registered, user_registration = UserRegistrationRepository().get_user_registration_details(
            address, airdrop_window_id
        )

        if isinstance(user_registration, list):
            logger.error(f"Find multiple registrations for {address=}, {airdrop_window_id=}")
            raise BadRequestException("Something wrong with user registration")

        last_claim = ClaimHistoryRepository().get_last_claim_history(
            airdrop_window_id=airdrop_window_id,
            address=address,
            blockchain_method="token_transfer"
        )

        last_ada_transfer = ClaimHistoryRepository().get_last_claim_history(
            airdrop_window_id=airdrop_window_id,
            address=address,
            blockchain_method="ada_transfer"
        )

        airdrop_claim_status = None
        if last_claim is not None:
            airdrop_claim_status = AirdropClaimStatus(last_claim.transaction_status)
        elif last_ada_transfer is not None:
            airdrop_claim_status = AirdropClaimStatus(last_ada_transfer.transaction_status)

        user_claim_status = UserRegistrationServices.__generate_user_claim_status(is_registered, airdrop_claim_status)

        registration_details = RegistrationDetails(
            registration_id = str(user_registration.receipt_generated),
            reject_reason = str(user_registration.reject_reason),
            other_details = user_registration.signature_details,
            registered_at = str(user_registration.registered_at)
        ) if is_registered and user_registration is not None else None

        window_registration_data = WindowRegistrationData(
            window_id=airdrop_window_id,
            airdrop_window_claim_status=airdrop_claim_status,
            claim_status=user_claim_status,
            registration_details=registration_details
        )

        return window_registration_data

    @staticmethod
    def eligibility_v2(inputs: dict) -> tuple:
        logger.info("Calling the user eligibility v2 check function")
        try:
            validate(instance=inputs, schema=ADDRESS_ELIGIBILITY_SCHEMA)

            airdrop_id = inputs["airdrop_id"]
            address = inputs["address"]
            signature = inputs.get("signature")
            timestamp = inputs.get("timestamp")
            wallet_name = inputs.get("wallet_name")
            key = inputs.get("key")

            if Utils.recognize_blockchain_network(address) == "Ethereum":
                address = Web3.to_checksum_address(address)

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if not airdrop:
                logger.error("Airdrop id is not valid")
                raise Exception("Airdrop id is not valid")

            airdrop_windows = AirdropWindowRepository().get_airdrop_windows(airdrop_id)
            if airdrop_windows is None:
                logger.error(f"No windows for aidrop: {airdrop_id}")
                raise Exception(f"No windows for aidrop: {airdrop_id}")

            airdrop_class = AirdropServices.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id)

            is_user_eligible = airdrop_object.check_user_eligibility(address)

            with_signature = False
            if signature is not None:
                airdrop_object.match_signature(
                    address=address,
                    signature=signature,
                    timestamp=timestamp,
                    wallet_name=wallet_name,
                    key=key
                )
                with_signature = True

            rewards_awarded = AirdropRepository().fetch_total_rewards_amount(airdrop_id, address)
            windows_registration_data: List[WindowRegistrationData] = []
            for window in airdrop_windows:
                windows_registration_data.append(
                    UserRegistrationServices.__get_registration_data(
                        address=address,
                        airdrop_window_id=window.id,
                    )
                )

            response = airdrop_object.generate_multiple_windows_eligibility_response(
                is_user_eligible=is_user_eligible,
                airdrop_id=airdrop_id,
                address=address,
                windows_registration_data = windows_registration_data,
                rewards_awarded=rewards_awarded,
                with_signature=with_signature
            )
        except (ValidationError, BaseException) as e:
            logger.exception(f"Error: {str(e)}")
            return HTTPStatus.BAD_REQUEST, str(e)
        return HTTPStatus.OK, response

    @staticmethod
    def eligibility(inputs: dict) -> tuple:
        logger.info("Calling the user eligibility check function")
        try:
            validate(instance=inputs, schema=ELIGIBILITY_SCHEMA)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if not airdrop:
                logger.error("Airdrop id is not valid")
                raise Exception("Airdrop id is not valid")

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id)
            if airdrop_window is None:
                logger.error("Airdrop window id is not valid")
                raise Exception("Airdrop window id is not valid")

            airdrop_class = AirdropServices.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            is_user_eligible = airdrop_object.check_user_eligibility(address)

            rewards_awarded = AirdropRepository().fetch_total_rewards_amount(airdrop_id, address)

            is_registered, user_registration = UserRegistrationRepository(). \
                get_user_registration_details(address, airdrop_window_id)

            is_airdrop_window_claimed = False
            is_claimable = False
            airdrop_claim_status = AirdropWindowRepository().is_airdrop_window_claimed(airdrop_window_id, address)

            if airdrop_claim_status == AirdropClaimStatus.SUCCESS.value:
                is_airdrop_window_claimed = True
            else:
                if rewards_awarded > 0:
                    is_claimable = True
            # if the user has not claimed yet and there are rewards pending to be claimed , then let the user claim
            # rewards awarded will have some value ONLY when the claim window opens and the user has unclaimed rewards
            # a claim in progress ~ PENDING will also be considered as claimed ( we don't want the user to end up losing
            # gas in trying to claim again)
            response = airdrop_object.generate_eligibility_response(
                airdrop_id=airdrop_id,
                airdrop_window_id=airdrop_window_id,
                address=address,
                is_user_eligible=is_user_eligible,
                is_registered=is_registered,
                user_registration=user_registration,
                is_airdrop_window_claimed=is_airdrop_window_claimed,
                airdrop_claim_status=airdrop_claim_status,
                rewards_awarded=rewards_awarded,
                is_claimable=is_claimable
            )
        except (ValidationError, BaseException) as e:
            logger.exception(f"Error: {str(e)}")
            return HTTPStatus.BAD_REQUEST, str(e)
        return HTTPStatus.OK, response

    @staticmethod
    def register(data: dict) -> tuple:
        logger.info("Calling the user registration function")
        try:
            validate(instance=data, schema=USER_REGISTRATION_SCHEMA)

            airdrop_id = data["airdrop_id"]
            airdrop_window_id = data["airdrop_window_id"]

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if not airdrop:
                logger.error("Airdrop id is not valid")
                raise Exception("Airdrop id is not valid")

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id)
            if airdrop_window is None:
                logger.error("Airdrop window id is not valid")
                raise Exception("Airdrop window id is not valid")

            airdrop_class = AirdropServices.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            response: list | str = airdrop_object.register(data=data)
        except (ValidationError, BaseException) as e:
            logger.exception(f"Error: {str(e)}")
            return HTTPStatus.BAD_REQUEST, str(e)
        return HTTPStatus.OK, response

    @staticmethod
    def update_registration(data) -> tuple:
        logger.info("Calling the user registration update function")
        try:
            validate(instance=data, schema=USER_REGISTRATION_SCHEMA)

            airdrop_id = data["airdrop_id"]
            airdrop_window_id = data["airdrop_window_id"]

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if not airdrop:
                logger.error("Airdrop id is not valid")
                raise Exception("Airdrop id is not valid")

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id)
            if airdrop_window is None:
                logger.error("Airdrop window id is not valid")
                raise Exception("Airdrop window id is not valid")

            airdrop_class = AirdropServices.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            response: dict | list | str = airdrop_object.update_registration(data=data)
        except TransactionNotFound as e:
            logger.exception(f"TransactionNotFound Error: {str(e)}")
            return HTTPStatus.NOT_FOUND, str(e)
        except (ValidationError, BaseException) as e:
            logger.exception(f"Error: {str(e)}")
            return HTTPStatus.BAD_REQUEST, str(e)
        return HTTPStatus.OK, response

    @staticmethod
    def check_trezor_registrations() -> None:
        logger.info("Calling the function to check the registration of Trezor wallets")
        pending_registration_repo = PendingTransactionRepository()
        pending_registrations = pending_registration_repo.get_all_pending_registrations()
        logger.info(f"Found {len(pending_registrations)} pending registrations to process")

        blockfrost = BlockFrostApi(project_id=BlockFrostAccountDetails.project_id,
                                   base_url=BlockFrostAPIBaseURL)
        to_delete: list[PendingTransaction] = list()
        to_save: list[PendingTransaction] = list()

        for registration in pending_registrations:
            logger.info(f"Processing pending registration {registration.id} for {registration.address}")
            try:
                tx_data = blockfrost.transaction(registration.tx_hash)
                tx_metadata = blockfrost.transaction_metadata(registration.tx_hash)
                tx_utxos = blockfrost.transaction_utxos(registration.tx_hash)

                registration_repo = UserRegistrationRepository()
                logger.info(f"Found tx {registration.tx_hash}: block={tx_data.block_height} index={tx_data.index}")
                is_registered, _ = registration_repo.get_user_registration_details(registration.address,
                                                                                   registration.airdrop_window_id)
                if is_registered:
                    logger.error("Address is already registered for this airdrop window")
                    raise Exception("Address is already registered for this airdrop window")

                # Transaction address check
                is_address_match = False
                for tx_input in tx_utxos.inputs:
                    if tx_input.address == registration.address:
                        is_address_match = True
                        break
                # Metadata check
                is_metadata_match, metadata = Utils().compare_data_from_db_and_metadata(
                    registration.signature_details,
                    tx_metadata
                )
                logger.info(f"Checks: {is_registered = } | {is_address_match = } | {is_metadata_match = }")
                if not is_registered and is_address_match and is_metadata_match:
                    logger.info(f"Registration to save {registration.id}")
                    registration.tx_metadata = metadata
                    to_save.append(registration)
                else:
                    logger.info(f"Registration to delete {registration.id}")
                    to_delete.append(registration)
            except BlockFrostApiError as error:
                logger.warning(f"Failed load transaction {registration.tx_hash} with blockfrost error {error}")
                row_created = registration.row_created.replace(tzinfo=datetime.timezone.utc)
                if datetime_in_utcnow() - row_created > datetime.timedelta(hours=48):
                    logger.warning(f"Transaction live time expired, deleted transaction {registration.tx_hash}")
                    to_delete.append(registration)
                continue

        logger.info(f"Amount of registrations to save: {len(to_save)}")
        for registration in to_save:
            registration_repo.register_user(
                airdrop_window_id=registration.airdrop_window_id,
                address=registration.address,
                receipt=registration.receipt_generated,
                tx_hash=registration.tx_hash,
                signature_details=registration.signature_details,
                block_number=registration.user_signature_block_number
            )
            to_delete.append(registration)

        logger.info(f"Amount of registrations to delete: {len(to_delete)}")
        pending_registration_repo.delete_pending_registrations(to_delete)
