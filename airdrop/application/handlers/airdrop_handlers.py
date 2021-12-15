from common.exception_handler import exception_handler
from airdrop.config import SLACK_HOOK, NETWORK_ID
from common.logger import get_logger
from common.utils import generate_lambda_response, request
from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.application.services.user_registration_services import UserRegistrationServices
from airdrop.application.services.user_notification_service import UserNotificationService


logger = get_logger(__name__)


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def get_airdrop_schedules(event, context):
    logger.info(f"Got Airdrops Event {event}")
    parameters = event['pathParameters']
    status, response = AirdropServices().get_airdrops_schedule(
        parameters['airdrop_id'])
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
def airdrop_window_claims(event, context):
    logger.info(f"Got Airdrops Window Claims Events {event}")
    status, response = AirdropServices(
    ).airdrop_window_claims(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def airdrop_window_claim_status(event, context):
    logger.info(f"Got Airdrops Window Claims Statys Events {event}")
    status, response = AirdropServices(
    ).airdrop_window_claim_status(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def airdrop_window_claim_history(event, context):
    logger.info(f"Got Airdrops Window Claims Statys Events {event}")
    status, response = AirdropServices(
    ).airdrop_window_claim_history(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def airdrop_event_listener(event, context):
    logger.info(f"Got Airdrops event listener {event}")
    status, response = AirdropServices(
    ).airdrop_listen_to_events(event)
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def airdrop_txn_watcher(event, context):
    logger.info(f"Got Airdrops txn status watcher {event}")
    AirdropServices().airdrop_txn_watcher()


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def user_notifications(event, context):
    logger.info(f"Got Airdrops user notifications {event}")
    status, response = UserNotificationService(
    ).subscribe_to_notifications(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )
