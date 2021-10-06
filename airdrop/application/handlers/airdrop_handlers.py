from common.exception_handler import exception_handler
from airdrop.config import SLACK_HOOK, NETWORK_ID
from common.logger import get_logger
from common.utils import generate_lambda_response, request
from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.application.services.user_registration_services import UserRegistrationServices


logger = get_logger(__name__)


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def get_airdrop_schedules(event, context):
    logger.info(f"Got Airdrops Event {event}")
    status, response = AirdropServices().get_airdrops_schedule(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def user_registration(event, context):
    logger.info(f"Got Airdrops Event {event}")
    status, response = UserRegistrationServices().register(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def user_eligibility(event, context):
    logger.info(f"Got Airdrops Event {event}")
    status, response = UserRegistrationServices().eligibility(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def get_active_airdrops(event, context):
    logger.info(f"Got Airdrops Event {event}")
    status, response = AirdropServices().get_airdrops(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def airdrop_window_user_details(event, context):
    logger.info(f"Got Airdrops Event {event}")
    status, response = UserRegistrationServices(
    ).airdrop_window_user_details(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )
