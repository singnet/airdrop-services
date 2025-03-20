import json

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from airdrop.processor.rejuve_airdrop import RejuveAirdrop


def test_match_signature():
    test_account = Account.create()
    private_key = test_account.key.hex()
    address = Web3.to_checksum_address(test_account.address)

    block_number = 123
    airdrop_id = 6
    airdrop_window_id = 24
    wallet_name = "Metamask"

    airdrop = RejuveAirdrop(airdrop_id, airdrop_window_id)

    message = {
        "airdropId": airdrop_id,
        "airdropWindowId": airdrop_window_id,
        "blockNumber": block_number,
        "walletAddress": address.lower(),
        "walletName": wallet_name,
    }

    message_str = json.dumps(message, separators=(",", ":"), sort_keys=True)
    encoded_message = encode_defunct(text=message_str)
    signed_message = Account.sign_message(encoded_message, private_key=private_key)
    signature = signed_message.signature.hex()

    formatted_message = airdrop.match_signature(
        signature=signature,
        address=address,
        block_number=block_number,
        wallet_name=wallet_name,
        key=None,
    )

    print("signature", signature)
    print("address", address)
    print("block_number", block_number)
    print("wallet_name", wallet_name)

    assert formatted_message == message
