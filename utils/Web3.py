import web3

from web3 import Web3
from config.infura import HTTP_PROVIDER
from eth_account.messages import defunct_hash_message, encode_defunct

web3_object = Web3(web3.providers.HTTPProvider(HTTP_PROVIDER))


def verify_signature(airdrop_id, airdrop_window_id, address, signature):
    public_key = recover_address(airdrop_id, airdrop_window_id, address, signature)

    if public_key.lower() != address.lower():
        raise Exception("Invalid signature")


def recover_address(airdrop_id, airdrop_window_id, address, signature):
    message = web3.Web3.soliditySha3(
        ["string", "string", "uint256"],
        [int(airdrop_id), int(airdrop_window_id), str(address)],
    )
    hash = defunct_hash_message(message)
    return web3_object.eth.account.recover_message(
        encode_defunct(hash), signature=signature
    )
