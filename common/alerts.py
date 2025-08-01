import json
import requests
from abc import ABC, abstractmethod
from functools import wraps
from common.constant import ERROR_MESSAGE_FORMAT
from common.logger import get_logger

logger = get_logger(__name__)


def delivery_exception_handler(method):

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            self.health_check()
            return method(self, *args, **kwargs)
        except AssertionError as e:
            logger.warning(f"Failed to send alert ({e})", exc_info=False)
        except Exception as e:
            logger.warning(f"Failed to send alert ({repr(e)})", exc_info=True)

    return wrapper


class AlertsProcessor(ABC):

    @property
    @abstractmethod
    def name(self):
        """Set the name of the alerts processor for external logging and debug"""
        return "Abstract"

    @abstractmethod
    def __init__(self):
        """Definition of all the parameters required to deliver notifications to the alert channel"""
        pass

    @abstractmethod
    def health_check(self):
        """Check that all processor parameters are set correctly for successful delivery
           !!! For each check use only assertions without AssertionError handling
        """
        assert True, "Check not passed"  # Use constructions like this to check all important points

    @abstractmethod
    def prepare_error_message(self, type: int, message: str) -> str:
        pass

    @abstractmethod
    def send(self, message: str):
        """Main method to deliver notification message to the alert channel"""
        pass


class SlackProcessor(AlertsProcessor):

    @property
    def name(self):
        return "Slack"

    def __init__(self, config: dict) -> None:
        self.msg_type = {0: "Info:: ", 1: "Err:: "}
        self.url = config.get("hostname") + config.get("path")
        self.channel = config.get("channel_name")
        self.username = "webhookbot"
        self.icon = ":ghost:"

    def health_check(self) -> None:
        assert self.url and isinstance(self.url, str), "Bad slack url value"
        assert self.channel and isinstance(self.channel, str), "Bad slack channel value"

    def prepare_error_message(self, network_id, query_string_parameters,
                              path, handler_name, path_parameters, body,
                              error_description) -> str:
        message = ERROR_MESSAGE_FORMAT.format(
            network_id=network_id,
            query_string_parameters=query_string_parameters,
            path=path,
            handler_name=handler_name,
            path_parameters=path_parameters,
            body=body,
            error_description=error_description
        )
        return f"```{message}```"

    @delivery_exception_handler
    def send(self, type: int, message: str) -> None:
        logger.info(f"Sending slack notification to #{self.channel}")
        prefix = self.msg_type.get(type, "")
        payload = {
            "channel": f"#{self.channel}",
            "username": self.username,
            "icon_emoji": self.icon,
            "text": prefix + message
        }
        response = requests.post(url=self.url, data=json.dumps(payload))
        logger.info(f"{self.name} response [code {response.status_code}]: {response.text}")


class MattermostProcessor(AlertsProcessor):

    @property
    def name(self):
        return "Mattermost"

    def __init__(self, config: dict) -> None:
        self.msg_type = {0: ":information_source: ", 1: ":warning: "}
        self.url = config.get("url")

    def health_check(self) -> None:
        assert self.url and isinstance(self.url, str), "Bad mattermost url value"

    def prepare_error_message(self, network_id, query_string_parameters,
                              path, handler_name, path_parameters, body,
                              error_description) -> str:
        message = ERROR_MESSAGE_FORMAT.format(
            network_id=network_id,
            query_string_parameters=query_string_parameters,
            path=path,
            handler_name=handler_name,
            path_parameters=path_parameters,
            body=body,
            error_description=error_description
        )
        return message

    @delivery_exception_handler
    def send(self, type: int, message: str) -> None:
        headers = {"Content-Type": "application/json"}
        prefix = "### " + self.msg_type.get(type, "")
        payload = {"text": prefix + message}
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        logger.info(f"{self.name} response [code {response.status_code}]: {response.text}")
