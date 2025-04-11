from logging import Logger
import sys
import traceback

from common.alerts import MattermostProcessor
from common.constant import ResponseStatus, StatusCode
from common.utils import generate_lambda_response


def extract_parameters_from_event(event):
    path = event.get("path", None)
    path_parameters = event.get("pathParameters", {})
    query_string_parameters = event.get("queryStringParameters", {})
    body = event.get("body", "{}")
    return path, path_parameters, query_string_parameters, body


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
    logger: Logger = decorator_kwargs["logger"]
    network_id: int | None = decorator_kwargs.get("NETWORK_ID", None)
    processor_config: dict = decorator_kwargs.get("PROCESSOR_CONFIG", {})
    exceptions: tuple = decorator_kwargs.get("EXCEPTIONS", ())
    raise_exception: bool = decorator_kwargs.get("RAISE_EXCEPTION", False)

    alert_processor = MattermostProcessor(config=processor_config)

    def decorator(func):
        def wrapper(*args, **kwargs):
            handler_name = decorator_kwargs.get("handler_name", func.__name__)
            event = kwargs.get("event", args[0] if len(args) > 0 else {})
            path, path_parameters, query_string_parameters, body = extract_parameters_from_event(event)
            error_description = ""
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                error_description = get_error_description(e)
                error_message = alert_processor.prepare_error_message(network_id=network_id,
                                                                      query_string_parameters=query_string_parameters,
                                                                      path=path,
                                                                      handler_name=handler_name,
                                                                      path_parameters=path_parameters,
                                                                      body=body,
                                                                      error_description=error_description)
                logger.exception(error_message)
                alert_processor.send(type=1, message=error_message)
                response_message = prepare_response_message(ResponseStatus.FAILED, error_message=e.error_message,
                                                            error_details=e.error_details)
                return generate_lambda_response(StatusCode.INTERNAL_SERVER_ERROR, response_message, cors_enabled=True)
            except Exception as e:
                error_description = get_error_description(e)
                error_message = alert_processor.prepare_error_message(network_id=network_id,
                                                                      query_string_parameters=query_string_parameters,
                                                                      path=path,
                                                                      handler_name=handler_name,
                                                                      path_parameters=path_parameters,
                                                                      body=body,
                                                                      error_description=error_description)
                logger.exception(error_message)
                alert_processor.send(type=1, message=error_message)
                response_message = prepare_response_message(ResponseStatus.FAILED, error_details=repr(e))
                if raise_exception:
                    raise e
                return generate_lambda_response(StatusCode.INTERNAL_SERVER_ERROR, response_message, cors_enabled=True)

        return wrapper

    return decorator
