from http import HTTPStatus

from jsonschema import validate, ValidationError

from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.constants import ELIGIBILITY_SCHEMA, USER_REGISTRATION_SCHEMA, AirdropClaimStatus
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.utils import Utils
from common.logger import get_logger

logger = get_logger(__name__)
utils = Utils()


class UserRegistrationServices:

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
