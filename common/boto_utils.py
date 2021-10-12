import boto3
import json

from botocore.config import Config
from botocore.exceptions import ClientError


from common.logger import get_logger

logger = get_logger(__name__)


class BotoUtils:
    def __init__(self, region_name):
        self.region_name = region_name

    def get_parameter_value_from_secrets_manager(self, secret_name):
        config = Config(retries=dict(max_attempts=2))
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager', region_name=self.region_name, config=config)
        try:
            parameter_value = client.get_secret_value(
                SecretId=secret_name)['SecretString']
        except ClientError as e:
            logger.error(f"Failed to fetch credentials {e}")
            raise e

        response = json.loads(parameter_value)
        return response[secret_name]
