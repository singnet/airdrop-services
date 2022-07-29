class StatusCode:
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
    CREATED = 201
    OK = 200


class ResponseStatus:
    FAILED = "failed"
    SUCCESS = "success"


SLACK_ERROR_MESSAGE_FORMAT = (
    "Error Reported! \n"
    "network_id: {network_id}\n"
    "path: {path}, \n"
    "handler: {handler_name} \n"
    "pathParameters: {path_parameters} \n"
    "queryStringParameters: {query_string_parameters} \n"
    "body: {body} \n"
    "x-ray-trace-id: None \n"
    "error_description: {error_description}\n"
)
