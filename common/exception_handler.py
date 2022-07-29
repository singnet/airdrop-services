import json
import sys
import traceback

from common.constant import SLACK_ERROR_MESSAGE_FORMAT, ResponseStatus, StatusCode
from common.utils import Utils, generate_lambda_response


def extract_parameters_from_event(event):
    path = event.get("path", None)
    path_parameters = event.get("pathParameters", {})
    query_string_parameters = event.get("queryStringParameters", {})
    body = event.get("body", "{}")
    return path, path_parameters, query_string_parameters, body


def prepare_slack_error_message(network_id, query_string_parameters, path, handler_name, path_parameters, body,
                                error_description):
    message = SLACK_ERROR_MESSAGE_FORMAT.format(network_id=network_id, query_string_parameters=query_string_parameters,
                                                path=path, handler_name=handler_name, path_parameters=path_parameters,
                                                body=body, error_description=error_description)
    return message


def get_error_description(e):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    exc_tb_lines = traceback.format_tb(exc_tb)
    error_description = repr(e) + "\n"
    for exc_lines in exc_tb_lines:
        error_description = error_description + exc_lines
    return error_description


def prepare_response_message(status, data="", code=0, error_message="", error_details=""):
    return {
        "status": ResponseStatus.FAILED,
        "data": data,
        "error": {
            "code": code,
            "message": error_message,
            "details": error_details
        }
    }


def exception_handler(*decorator_args, **decorator_kwargs):
    logger = decorator_kwargs["logger"]
    network_id = decorator_kwargs.get("NETWORK_ID", None)
    slack_hook = decorator_kwargs.get("SLACK_HOOK", None)
    exceptions = decorator_kwargs.get("EXCEPTIONS", ())
    raise_exception = decorator_kwargs.get("RAISE_EXCEPTION", False)

    def decorator(func):
        def wrapper(*args, **kwargs):
            handler_name = decorator_kwargs.get("handler_name", func.__name__)
            event = kwargs.get("event", args[0] if len(args) >0 else {})
            path, path_parameters, query_string_parameters, body = extract_parameters_from_event(event)
            error_description = ""
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                error_description = get_error_description(e)
                slack_error_message = prepare_slack_error_message(network_id=network_id,
                                                            query_string_parameters=query_string_parameters,
                                                            path=path, handler_name=handler_name,
                                                            path_parameters=path_parameters,
                                                            body=body, error_description=error_description)
                slack_message = f"```{slack_error_message}```"
                logger.exception(slack_error_message)
                Utils().report_slack(type=0, slack_message=slack_message, slack_config=slack_hook)
                response_message = prepare_response_message(ResponseStatus.FAILED, error_message=e.error_message,
                                                            error_details=e.error_details)
                return generate_lambda_response(StatusCode.INTERNAL_SERVER_ERROR, response_message, cors_enabled=True)
            except Exception as e:
                error_description = get_error_description(e)
                slack_error_message = prepare_slack_error_message(network_id=network_id,
                                                            query_string_parameters=query_string_parameters,
                                                            path=path, handler_name=handler_name,
                                                            path_parameters=path_parameters,
                                                            body=body, error_description=error_description)
                logger.exception(slack_error_message)
                slack_message = f"```{slack_error_message}```"
                logger.exception(slack_error_message)
                Utils().report_slack(type=0, slack_message=slack_message, slack_config=slack_hook)
                response_message = prepare_response_message(ResponseStatus.FAILED, error_details=repr(e))
                if raise_exception:
                    raise e
                return generate_lambda_response(StatusCode.INTERNAL_SERVER_ERROR, response_message, cors_enabled=True)

        return wrapper

    return decorator
