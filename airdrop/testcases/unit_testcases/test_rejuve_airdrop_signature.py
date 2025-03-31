import json
from time import time

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from airdrop.processor.rejuve_airdrop import RejuveAirdrop


def test_match_signature():
    test_account = Account.create()
    private_key = test_account.key.hex()
    address = Web3.to_checksum_address(test_account.address)

    timestamp = int(time())
    airdrop_id = 6
    airdrop_window_id = 24
    wallet_name = "Metamask"

    airdrop = RejuveAirdrop(airdrop_id, airdrop_window_id)

    message = {
        "airdropId": airdrop_id,
        "airdropWindowId": airdrop_window_id,
        "timestamp": timestamp,
        "walletAddress": address.lower(),
        "walletName": wallet_name,
    }

    original_message = json.dumps(message, separators=(',', ':'))
    encoded_message = encode_defunct(text=original_message)
    signed_message = Account.sign_message(encoded_message, private_key=private_key)
    signature = signed_message.signature.hex()

    formatted_message = airdrop.match_signature(
        address=address,
        signature=signature,
        timestamp=timestamp,
        wallet_name=wallet_name,
        key=None
    )

    print("formatted_message", formatted_message)
    print("original_message", original_message)

    assert formatted_message == message
