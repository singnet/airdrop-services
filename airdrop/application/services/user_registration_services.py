from http import HTTPStatus
from typing import List

from jsonschema import validate, ValidationError

from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.constants import (
    ELIGIBILITY_SCHEMA,
    ADDRESS_ELIGIBILITY_SCHEMA,
    USER_REGISTRATION_SCHEMA,
    AirdropClaimStatus,
    UserClaimStatus
)
from airdrop.application.types.windows import WindowRegistrationData, RegistrationDetails
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.utils import Utils
from common.logger import get_logger

logger = get_logger(__name__)
utils = Utils()


class UserRegistrationServices:

    @staticmethod
    def __generate_user_claim_status(
        user_registered: bool,
        airdrop_claim_status: AirdropClaimStatus | None,
    ) -> UserClaimStatus:
        logger.debug(
            f"Generate user claim status. \
            user_registerd: {user_registered}, \
            airdrop_claim_status: {airdrop_claim_status}")
        if not user_registered:
            return UserClaimStatus.NOT_REGISTERED
        elif airdrop_claim_status == AirdropClaimStatus.SUCCESS:
            return UserClaimStatus.RECEIVED
        elif airdrop_claim_status in (
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
        user_registered, user_registration = UserRegistrationRepository().get_user_registration_details(address, airdrop_window_id)

        airdrop_claim_status = AirdropWindowRepository().is_airdrop_window_claimed(airdrop_window_id, address)

        user_claim_status = UserRegistrationServices.__generate_user_claim_status(user_registered, airdrop_claim_status)

        registration_details = RegistrationDetails(
            registration_id=user_registration.receipt_generated,
            reject_reason=user_registration.reject_reason,
            other_details=user_registration.signature_details,
            registered_at=str(user_registered.registered_at)
        ) if user_registered and user_registration is not None else None

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
            address = inputs["address"].lower()
            signature = inputs.get("signature")
            block_number = inputs.get("block_number")
            wallet_name = inputs.get("wallet_name")
            key = inputs.get("key")

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

            is_user_eligible = airdrop_object.check_user_eligibility(
                address,
                [window.id for window in airdrop_windows]
            )

            with_signature = False
            if signature is not None:
                airdrop_object.match_signature(
                    address=address,
                    signature=signature,
                    block_number=block_number,
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

            user_registered, user_registration = UserRegistrationRepository(). \
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
                user_registered=user_registered,
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
    def register(inputs: dict) -> tuple:
        logger.info("Calling the user registration function")
        try:
            validate(instance=inputs, schema=USER_REGISTRATION_SCHEMA)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]

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

            response: list | str = airdrop_object.register(inputs)
        except (ValidationError, BaseException) as e:
            logger.exception(f"Error: {str(e)}")
            return HTTPStatus.BAD_REQUEST, str(e)
        return HTTPStatus.OK, response

    @staticmethod
    def update_registration(inputs) -> tuple:
        logger.info("Calling the user registration update function")
        try:
            validate(instance=inputs, schema=USER_REGISTRATION_SCHEMA)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]

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

            response: list | str = airdrop_object.update_registration(inputs)
        except (ValidationError, BaseException) as e:
            logger.exception(f"Error: {str(e)}")
            return HTTPStatus.BAD_REQUEST, str(e)
        return HTTPStatus.OK, response
