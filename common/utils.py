import datetime
import json
import sys
import traceback

import requests
import web3
from web3 import Web3
from eth_account.messages import defunct_hash_message, encode_defunct
from airdrop.config import NETWORK
from http import HTTPStatus
from common.logger import get_logger

logger = get_logger(__name__)


class Utils:
    def __init__(self):
        self.msg_type = {0: "Info:: ", 1: "Err:: "}

    def report_slack(self, type, slack_message, slack_config):
        url = slack_config["hostname"] + slack_config["path"]
        prefix = self.msg_type.get(type, "")
        slack_channel = slack_config.get("channel", "contract-index-alerts")
        print(url)
        payload = {
            "channel": f"#{slack_channel}",
            "username": "webhookbot",
            "text": prefix + slack_message,
            "icon_emoji": ":ghost:",
        }

        resp = requests.post(url=url, data=json.dumps(payload))
        print(resp.status_code, resp.text)

    @staticmethod
    def remove_http_https_prefix(url):
        url = url.replace("https://", "")
        url = url.replace("http://", "")
        return url

    @staticmethod
    def get_current_block_no(ws_provider):
        w3Obj = Web3(web3.providers.WebsocketProvider(ws_provider))
        return w3Obj.eth.blockNumber


def make_response(status_code, body, header=None):
    return {"statusCode": status_code, "headers": header, "body": body}


def validate_dict(data_dict, required_keys, strict=False):
    for key in required_keys:
        if key not in data_dict:
            return False

    if strict:
        return validate_dict(required_keys, data_dict.keys())

    return True


def validate_dict_list(data_list, required_keys):
    for data in data_list:
        if not validate_dict(data, required_keys):
            return False
    return True


def make_response_body(status, data, error):
    return {"status": status, "data": data, "error": error}


def request(event):
    try:
        inputs = event["body"] or None
        if inputs is not None:
            return json.loads(inputs)
        else:
            return None
    except Exception as e:
        print(str(e))
        return None


def generate_lambda_response(
    status_code, message, data=None, headers=None, cors_enabled=False
):

    if HTTPStatus.OK.value >= status_code and status_code <= HTTPStatus.ALREADY_REPORTED.value:
        body = {"status": status_code, "data": data, "message": message}
    else:
        body = {
            "error": {"code": 0, "message": data},
            "data": None,
            "status": status_code,
        }

    response = {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"},
    }
    if cors_enabled:
        response["headers"].update(
            {
                "X-Requested-With": "*",
                "Access-Control-Allow-Headers": "Access-Control-Allow-Origin, Content-Type, X-Amz-Date, Authorization,"
                "X-Api-Key,x-requested-with",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,OPTIONS,POST",
            }
        )
    if headers is not None:
        response["headers"].update(headers)
    return response


def extract_payload(method, event):
    method_found = True
    payload_dict = None
    path_parameters = event.get("pathParameters", None)
    if method == "POST":
        payload_dict = json.loads(event["body"])
    elif method == "GET":
        payload_dict = event.get("queryStringParameters", {})
    else:
        method_found = False
    return method_found, path_parameters, payload_dict


def format_error_message(status, error, payload, net_id, handler=None, resource=None):
    return json.dumps(
        {
            "status": status,
            "error": error,
            "resource": resource,
            "payload": payload,
            "network_id": net_id,
            "handler": handler,
        }
    )


def handle_exception_with_slack_notification(*decorator_args, **decorator_kwargs):
    logger = decorator_kwargs["logger"]
    NETWORK_ID = decorator_kwargs.get("NETWORK_ID", None)
    SLACK_HOOK = decorator_kwargs.get("SLACK_HOOK", None)
    IGNORE_EXCEPTION_TUPLE = decorator_kwargs.get("IGNORE_EXCEPTION_TUPLE", ())

    def decorator(func):
        def wrapper(*args, **kwargs):
            handler_name = decorator_kwargs.get("handler_name", func.__name__)
            path = kwargs.get("event", {}).get("path", None)
            path_parameters = kwargs.get("event", {}).get("pathParameters", {})
            query_string_parameters = kwargs.get("event", {}).get(
                "queryStringParameters", {}
            )
            body = kwargs.get("event", {}).get("body", "{}")
            payload = {
                "pathParameters": path_parameters,
                "queryStringParameters": query_string_parameters,
                "body": json.loads(body),
            }
            try:
                return func(*args, **kwargs)
            except IGNORE_EXCEPTION_TUPLE as e:
                logger.exception(
                    "Exception is part of IGNORE_EXCEPTION list. Error description: %s",
                    repr(e),
                )
                return generate_lambda_response(
                    status_code=500,
                    message=format_error_message(
                        status="failed",
                        error=repr(e),
                        payload=payload,
                        net_id=NETWORK_ID,
                        handler=handler_name,
                    ),
                    cors_enabled=True,
                )
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                slack_msg = (
                    f"\n```Error Reported !! \n"
                    f"network_id: {NETWORK_ID}\n"
                    f"path: {path}, \n"
                    f"handler: {handler_name} \n"
                    f"pathParameters: {path_parameters} \n"
                    f"queryStringParameters: {query_string_parameters} \n"
                    f"body: {body} \n"
                    f"x-ray-trace-id: None \n"
                    f"error_description: {repr(traceback.format_tb(tb=exc_tb))}```"
                )

                logger.exception(f"{slack_msg}")
                Utils().report_slack(type=0, slack_msg=slack_msg, SLACK_HOOK=SLACK_HOOK)
                return generate_lambda_response(
                    status_code=500,
                    message=format_error_message(
                        status="failed",
                        error=repr(e),
                        payload=payload,
                        net_id=NETWORK_ID,
                        handler=handler_name,
                    ),
                    cors_enabled=True,
                )

        return wrapper

    return decorator


def json_to_file(payload, filename):
    with open(filename, "w") as f:
        f.write(json.dumps(payload, indent=4))


def datetime_to_string(given_time):
    return given_time.strftime("%Y-%m-%d %H:%M:%S")


def date_time_for_filename():
    return datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")


def send_slack_notification(slack_message, slack_url, slack_channel):
    payload = {
        "channel": f"#{slack_channel}",
        "username": "webhookbot",
        "text": slack_message,
        "icon_emoji": ":ghost:",
    }
    slack_response = requests.post(url=slack_url, data=json.dumps(payload))
    logger.info(
        f"slack response :: {slack_response.status_code}, {slack_response.text}"
    )


def get_transaction_receipt_from_blockchain(transaction_hash):
    web3_object = Web3(web3.providers.HTTPProvider(
        NETWORK['http_provider']))
    return web3_object.eth.getTransactionReceipt(transaction_hash)


def generate_claim_signature(amount, airdrop_id, airdrop_window_id, user_address, contract_address, token_address, private_key):
    try:
        user_address = Web3.toChecksumAddress(user_address)
        token_address = Web3.toChecksumAddress(token_address)
        contract_address = Web3.toChecksumAddress(contract_address)
        message = web3.Web3.soliditySha3(
            ["string", "uint256", "address", "uint256",
                "uint256", "address", "address"],
            ["__airdropclaim", int(amount), user_address, int(airdrop_id),
             int(airdrop_window_id), contract_address, token_address],
        )

        message_hash = encode_defunct(message)

        web3_object = Web3(web3.providers.HTTPProvider(
            NETWORK['http_provider']))
        signed_message = web3_object.eth.account.sign_message(
            message_hash, private_key=private_key)

        return signed_message.signature.hex()
    except BaseException as e:
        raise Exception(f"Error while generating claim signature. Error: {e}")


def load_contract(path):
    with open(path) as f:
        contract = json.load(f)
    return contract


def read_contract_address(net_id, path, key):
    contract = load_contract(path)
    return Web3.toChecksumAddress(contract[str(net_id)][key])


def verify_signature(airdrop_id, airdrop_window_id, address, signature):
    public_key = recover_address(
        airdrop_id, airdrop_window_id, address, signature)

    if public_key.lower() != address.lower():
        raise Exception("Invalid signature")


def recover_address(airdrop_id, airdrop_window_id, address, signature):
    address = Web3.toChecksumAddress(address)
    message = web3.Web3.soliditySha3(
        ["uint8", "uint8", "address"],
        [int(airdrop_id), int(airdrop_window_id), address],
    )
    hash = defunct_hash_message(message)
    web3_object = Web3(web3.providers.HTTPProvider(NETWORK['http_provider']))
    return web3_object.eth.account.recoverHash(
        hash, signature=signature
    )
