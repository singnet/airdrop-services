import sys

sys.path.append('/opt')
from airdrop.config import MATTERMOST_CONFIG, NETWORK_ID
from airdrop.application.services.event_consumer_service import DepositEventConsumerService
from common.logger import get_logger
from common.utils import generate_lambda_response
from common.exception_handler import exception_handler
from common.exceptions import ValidationFailedException

logger = get_logger(__name__)
EXCEPTIONS = (ValidationFailedException,)


@exception_handler(PROCESSOR_CONFIG=MATTERMOST_CONFIG, NETWORK_ID=NETWORK_ID, logger=logger, EXCEPTIONS=EXCEPTIONS,
                   RAISE_EXCEPTION=True)
def deposit_event_consumer(event, context):
    logger.info(f"Got deposit event {event}")
    response = DepositEventConsumerService(event).validate_deposit_event()
    return generate_lambda_response(200, response)
