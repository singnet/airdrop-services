import sys

sys.path.append('/opt')
import json
import requests
from http import HTTPStatus
from common.exception_handler import exception_handler
from airdrop.config import SLACK_HOOK, NETWORK_ID, MIN_BLOCK_CONFIRMATION_REQUIRED, BlockFrostAPI, \
    BlockFrostAccountDetails
from airdrop.application.services.event_consumer_service import DepositEventConsumerService
from common.logger import get_logger
from common.utils import generate_lambda_response

logger = get_logger(__name__)


@exception_handler(SLACK_HOOK=SLACK_HOOK, NETWORK_ID=NETWORK_ID, logger=logger)
def deposit_event_consumer(event, context):
    logger.info(f"Got deposit event {event}")
    DepositEventConsumerService(event).validate_deposit_event()
    status = HTTPStatus.OK
    return generate_lambda_response(200, status)

#
# if __name__ == '__main__':
#     event = {'Records': [{'messageId': 'e7ccb647-8820-43e5-9d88-19f75a5bd390',
#                           'receiptHandle': 'AQEBEM2ydV3lYNhj+/6KeEeqBC2qkdyxrDQ9GrWmnbgJoWr2M9GEZaXTdyDUcheQCHokWkQP40Bf7XjIc8A+O5Sp3DCZAcWQb0AvkGspWR5GNcaTIJvq4PysTLiio7i006qzvsk9Vsx9x9kLGKNDld9kE6WIn0wP6ReP7dw8hUtynyQ1gF6/7BqCMzmMmwoNcOgFDTlrJKSg3hO4P8Zj5qp4OCYcg1R5wPPKeALSDMsFZfxPxp5nfWb8oOlo1Jq2vUfWcjqYjlZ1Med2dKfsU8S/h4uMhBqVkXLYaiY+T3end3E5R4zTtPk3OAIwbq/a31Fqk3h5Zr7Ng1GLz+aLbz3khqdGjGQJ//j8BTC3kCjZ7lUIZzBwRYhKQapzHAvdAYLGJdFnGBE+h+cuxfPGjHVbdjnrOpA+MQpkeig2Zzhu180=',
#                           'body': '{\n  "Type" : "Notification",\n  "MessageId" : "4ffadeda-b19a-57a0-9c0f-8589df44a185",\n  "TopicArn" : "arn:aws:sns:us-east-1:533793137436:rt-v2-cardano-event-listener",\n  "Message" : "{\\"id\\": \\"3b6a67197c6c412c952b5486156148e6\\", \\"tx_hash\\": \\"edf5f74112670b7b5f8c003a42bcbc410d35abbee2d6566068a1c30201d0f735\\", \\"event_type\\": \\"TOKEN_TRANSFER\\", \\"address\\": \\"addr_test1qqllt2lmzypu9y9j9p6hgrcu9narh8rqczkdujqvqmqq4f9w9zv7f7pu6wefmn4t06y9e9ljggpjul3awg0p8tz664fse7qsex\\", \\"event_status\\": null, \\"updated_at\\": \\"2022-07-21 15:09:32\\", \\"asset\\": {\\"id\\": \\"1aa646b44ce44febba7b75f8716339c7\\", \\"asset\\": \\"6f1a1f0c7ccf632cc9ff4b79687ed13ffe5b624cce288b364ebdce5041474958\\", \\"policy_id\\": \\"6f1a1f0c7ccf632cc9ff4b79687ed13ffe5b624cce288b364ebdce50\\", \\"asset_name\\": \\"41474958\\", \\"allowed_decimal\\": 8, \\"updated_at\\": \\"2022-03-17 12:51:13\\"}, \\"transaction_detail\\": {\\"id\\": \\"dcdd4145cb4840baa44e2dce8a404839\\", \\"tx_type\\": \\"TOKEN_RECEIVED\\", \\"assurance_level\\": \\"LOW\\", \\"confirmations\\": 3, \\"tx_amount\\": \\"1E+8\\", \\"tx_fee\\": \\"191681\\", \\"block_number\\": 3724538, \\"block_time\\": 1658416153, \\"tx_metadata\\": [], \\"updated_at\\": \\"2022-07-21 15:11:26\\"}}",\n  "Timestamp" : "2022-07-21T15:11:26.116Z",\n  "SignatureVersion" : "1",\n  "Signature" : "tA6XbO0uJhV5efk1BlyHgJYE4HSI5Pv3doH2plD+noYyqabvruEzJKe04bZmc3oLpSBNC3YzJ+VBwgQcmJdtzq9ICsHSVoSzZW+ipZot9uuc1lZkunB7SCptfel59BHFvoy3mukTUsFIEZhjspMHWDOXmSIdYExjqeDH/K1+rK5ClpGfrqD1tGhfFUMgZG4jKWKvfBshTs1YpH2L9ojsZN212b6bG7CdZHCSJ2OIVq7ss1mLsMRM1fdyr8xsZj99SG3YN74KfuY6cOKzCKimX5pTZ00bfxb9I63T4KRkuO0PyUkEuZ+BpsX00PsufW0fycR5RL8jUPJTobOVU2q6rA==",\n  "SigningCertURL" : "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-7ff5318490ec183fbaddaa2a969abfda.pem",\n  "UnsubscribeURL" : "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:533793137436:rt-v2-cardano-event-listener:64c08022-85d9-4b22-a347-c2f91adf455a"\n}',
#                           'attributes': {'ApproximateReceiveCount': '1', 'SentTimestamp': '1658416286154',
#                                          'SenderId': 'AIDAIT2UOQQY3AUEKVGXU',
#                                          'ApproximateFirstReceiveTimestamp': '1658416286157'}, 'messageAttributes': {},
#                           'md5OfBody': 'd57fdf832148fabee6330cadaf72eb74', 'eventSource': 'aws:sqs',
#                           'eventSourceARN': 'arn:aws:sqs:us-east-1:533793137436:Staging-cardano-event-consumer',
#                           'awsRegion': 'us-east-1'}]}
#     deposit_event_consumer(event, None)
