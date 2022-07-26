import sys
sys.path.append('/opt')

from http import HTTPStatus
from common.exception_handler import exception_handler
from airdrop.config import SLACK_HOOK, NETWORK_ID
from common.logger import get_logger
from common.utils import generate_lambda_response

logger = get_logger(__name__)


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def deposit_event_consumer(event, context):
    logger.info(f"Got deposit event {event}")
    status = HTTPStatus.OK
    return generate_lambda_response(200, status)