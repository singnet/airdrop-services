from airdrop.processor.loyalty_airdrop import LoyaltyAirdrop
from airdrop.constants import USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data


def test_match_signature():
    test_account = Account.create()
    private_key = test_account.key.hex()
    address = test_account.address.lower()
    address = Web3.to_checksum_address(address)

    block_number = 123
    airdrop_id = 0
    aidrop_window_id = 0
    cardano_address = "test"
    cardano_wallet_name = "test"

    airdrop = LoyaltyAirdrop(airdrop_id, aidrop_window_id)

    message = USER_REGISTRATION_SIGNATURE_LOYALTY_AIRDROP_FORMAT
    message["message"] = {
        "Airdrop": {
            "airdropId": airdrop_id,
            "airdropWindowId": aidrop_window_id,
            "blockNumber": block_number,
            "walletAddress": Web3.to_checksum_address(address),
            "cardanoAddress": cardano_address,
            "cardanoWalletName": cardano_wallet_name,
        },
    }
    message["domain"]["name"] = "SingularityNet"

    encoded_message = encode_typed_data(full_message=message)
    signed_message = Account.sign_message(encoded_message, private_key=private_key)
    signature = signed_message.signature.hex()

    formatted_message = airdrop.match_signature(
        address,
        signature,
        block_number,
        cardano_address=cardano_address,
        cardano_wallet_name=cardano_wallet_name,
    )

    assert formatted_message == message
