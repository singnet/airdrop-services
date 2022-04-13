import datetime
import json
import sys
import traceback
from base64 import b64encode

import requests
import web3
from web3 import Web3
from enum import Enum
from eth_account.messages import defunct_hash_message, encode_defunct
from airdrop.config import NETWORK
from http import HTTPStatus
from common.logger import get_logger
from airdrop.config import SLACK_HOOK

logger = get_logger(__name__)


class ContractType(Enum):
    STAKING = "STAKING"
    AIRDROP = "AIRDROP"


class Utils:
    def __init__(self):
        self.msg_type = {0: "Info:: ", 1: "Err:: "}

    def report_slack(self, type, slack_message, slack_config):
        url = slack_config["hostname"] + slack_config["path"]
        prefix = self.msg_type.get(type, "")
        slack_channel = slack_config.get("channel", SLACK_HOOK['channel_name'])
        print(url)
        payload = {
            "channel": f"#{slack_channel}",
            "username": "webhookbot",
            "text": prefix + slack_message,
            "icon_emoji": ":ghost:",
        }

        resp = requests.post(url=url, data=json.dumps(payload))
        print(resp.status_code, resp.text)


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


def json_to_file(payload, filename):
    with open(filename, "w") as f:
        f.write(json.dumps(payload, indent=4))


def get_transaction_receipt_from_blockchain(transaction_hash):
    web3_object = Web3(web3.providers.HTTPProvider(
        NETWORK['http_provider']))
    return web3_object.eth.getTransactionReceipt(transaction_hash)

#TODO this will need to be deleted , after the nunet OCCAM claims windows expire
def generate_claim_signature(amount, airdrop_id, airdrop_window_id, user_address, contract_address, token_address, private_key):
    try:
        user_address = Web3.toChecksumAddress(user_address)
        token_address = Web3.toChecksumAddress(token_address)
        contract_address = Web3.toChecksumAddress(contract_address)

        print("Generate claim signature user_address: ", user_address)
        print("Generate claim signature token_address: ", token_address)
        print("Generate claim signature contract_address: ", contract_address)

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
        raise e(f"Error while generating claim signature. Error: {e}")

def generate_claim_signature_with_total_eligibile_amount(totalEligibleAmount,airdropAmount, airdrop_id,
                                                         airdrop_window_id, user_address,
                                                         contract_address, token_address, private_key):
    try:
        user_address = Web3.toChecksumAddress(user_address)
        token_address = Web3.toChecksumAddress(token_address)
        contract_address = Web3.toChecksumAddress(contract_address)

        print("Generate secured claim signature user_address: ", user_address)
        print("Generate secured claim signature token_address: ", token_address)
        print("Generate secured claim signature contract_address: ", contract_address)

        message = web3.Web3.soliditySha3(
            ["string","uint256","uint256", "address", "uint256",
                "uint256", "address", "address"],
            ["__airdropclaim",int(totalEligibleAmount) ,int(airdropAmount), user_address, int(airdrop_id),
             int(airdrop_window_id), contract_address, token_address],
        )

        message_hash = encode_defunct(message)

        web3_object = Web3(web3.providers.HTTPProvider(
            NETWORK['http_provider']))
        signed_message = web3_object.eth.account.sign_message(
            message_hash, private_key=private_key)

        return signed_message.signature.hex()
    except BaseException as e:
        raise e(f"Error while generating claim signature. Error: {e}")

def load_contract(path):
    with open(path) as f:
        contract = json.load(f)
    return contract


def read_contract_address(net_id, path, key):
    contract = load_contract(path)
    return Web3.toChecksumAddress(contract[str(net_id)][key])


def get_checksum_address(address):
    return Web3.toChecksumAddress(address)


def get_contract_file_paths(base_path, contract_name):
    logger.info(f"base_path: {base_path}")

    if contract_name == ContractType.STAKING.value:
        json_file = "SDAOBondedTokenStake.json"
    elif contract_name == ContractType.AIRDROP.value:
        json_file = "SingularityAirdrop.json"
    else:
        raise Exception("Invalid contract Type {}".format(contract_name))

    contract_network_path = base_path + "/{}/{}".format("networks", json_file)
    contract_abi_path = base_path + "/{}/{}".format("abi", json_file)

    return contract_network_path, contract_abi_path


def contract_instance(contract_abi, address):
    provider = Web3.HTTPProvider(NETWORK['http_provider'])
    web3_object = Web3(provider)
    return web3_object.eth.contract(abi=contract_abi, address=address)


def get_contract_instance(base_path, contract_address, contract_name):
    contract_network_path, contract_abi_path = get_contract_file_paths(
        base_path, contract_name)

    contract_abi = load_contract(contract_abi_path)
    logger.debug(f"contract address is {contract_address}")
    provider = Web3.HTTPProvider(NETWORK['http_provider'])
    web3_object = Web3(provider)
    return web3_object.eth.contract(abi=contract_abi, address=contract_address)


def verify_signature(airdrop_id, airdrop_window_id, address, signature, block_number):
    public_key = recover_address(
        airdrop_id, airdrop_window_id, address, signature, block_number)

    if public_key.lower() != address.lower():
        logger.info(f"INVALID SIGNATURE {signature}")
        logger.info(f"For airdrop_id:{airdrop_id} , airdrop_window_id:{airdrop_window_id} , address:{address} , "
                    f"block_number{block_number}")
        #raise Exception("Invalid signature")


def recover_address(airdrop_id, airdrop_window_id, address, signature, block_number):
    address = Web3.toChecksumAddress(address)
    message = web3.Web3.soliditySha3(
        ["uint256", "uint256", "uint256", "address"],
        [int(airdrop_id), int(airdrop_window_id), int(block_number), address],
    )
    hash_message = defunct_hash_message(message)
    web3_object = Web3(web3.providers.HTTPProvider(NETWORK['http_provider']))
    return web3_object.eth.account.recoverHash(
        hash_message, signature=signature
    )


def get_registration_receipt(airdrop_id, airdrop_window_id, user_address, private_key):
    try:
        user_address = Web3.toChecksumAddress(user_address)

        message = web3.Web3.soliditySha3(
            ["string", "address", "uint256", "uint256"],
            ["__receipt_ack_message", user_address, int(airdrop_id), int(airdrop_window_id)],
        )

        message_hash = encode_defunct(message)

        web3_object = Web3(web3.providers.HTTPProvider(
            NETWORK['http_provider']))
        signed_message = web3_object.eth.account.sign_message(
            message_hash, private_key=private_key)
        return b64encode(signed_message.signature).decode()

    except BaseException as e:
        raise e
