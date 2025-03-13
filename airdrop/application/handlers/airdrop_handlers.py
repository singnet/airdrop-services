import sys

sys.path.append('/opt')

from common.exception_handler import exception_handler
from airdrop.config import SLACK_HOOK, NETWORK_ID
from common.logger import get_logger
from common.utils import generate_lambda_response, request
from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.application.services.user_registration_services import UserRegistrationServices
from airdrop.application.services.user_notification_service import UserNotificationService
from airdrop.application.services.user_claim_service import UserClaimService

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
def user_registration_update(event, context):
    logger.info(f"Got Airdrops Event {event}")
    status, response = UserRegistrationServices().update_registration(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def airdrop_window_stake_details(event, context):
    logger.info(f"Got Airdrops Window Stake details {event}")
    status, response = AirdropServices().get_airdrop_window_stake_details(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def address_eligibility(event, context):
    logger.info(f"Got Airdrops Event {event}")
    status, response = UserRegistrationServices().eligibility_v2(request(event))
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
def occam_airdrop_window_claim(event, context):
    logger.info(f"Got occam_airdrop_window_claim event {event}")
    status, response = AirdropServices().occam_airdrop_window_claim(request(event))
    return generate_lambda_response(
        status.value,
        status.phrase,
        response,
        cors_enabled=True,
    )


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def airdrop_window_claim(event, context):
    logger.info(f"Got airdrop_window_claim Events {event}")
    status, response = AirdropServices().airdrop_window_claim(request(event))
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
def airdrop_event_consumer(event, context):
    logger.info(f"Got Airdrops event listener {event}")
    status, response = AirdropServices(
    ).airdrop_event_consumer(event)
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


def cardano_airdrop_transfer_claim_service(event, context):
    logger.info(f"Initiate claims event {event}")
    airdrop_id = event["airdrop_id"]
    UserClaimService(airdrop_id).initiate_claim_for_users()
    logger.info("success")


def update_user_claim_transaction_status_post_block_confirmation(event, context):
    logger.info(f"Update claim transaction statuses event {event}")
    airdrop_id = event["airdrop_id"]
    UserClaimService(airdrop_id).update_user_claim_transaction_status_post_block_confirmation()
    logger.info("success")
