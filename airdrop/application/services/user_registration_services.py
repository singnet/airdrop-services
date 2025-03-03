from http import HTTPStatus

from jsonschema import validate, ValidationError

from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.constants import ELIGIBILITY_SCHEMA, USER_REGISTRATION_SCHEMA
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
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

            response: dict | str = airdrop_object.eligibility(inputs)
        except (ValidationError, BaseException) as e:
            logger.exception(f"Error: {e}")
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
            logger.exception(f"Error: {e}")
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
            logger.exception(f"Error: {e}")
            return HTTPStatus.BAD_REQUEST, str(e)
        return HTTPStatus.OK, response
