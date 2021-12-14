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
        try:
            config = Config(retries=dict(max_attempts=2))
            client = boto3.client(
                service_name='secretsmanager', region_name=self.region_name, config=config)
            parameter_value = client.get_secret_value(
                SecretId=secret_name)['SecretString']
            print(f"Retrieved values {parameter_value}")
        except ClientError as e:
            logger.error(f"Failed to fetch credentials {e}")
            raise e

        response = json.loads(parameter_value)
        return response[secret_name]
