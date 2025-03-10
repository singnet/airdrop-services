from datetime import datetime, timezone

from eth_account.messages import encode_defunct, encode_typed_data
from pycardano import cip8
from web3 import Web3

from common.logger import get_logger

logger = get_logger(__name__)


def datetime_in_utcnow():
    return datetime.now(timezone.utc)



class Utils:

    @staticmethod
    def match_ethereum_signature_eip191(
        address: str,
        formatted_message: str,
        signature: str
    ) -> tuple[bool, str]:
        logger.info("Ethereum Signature Comparison EIP-191")
        signature_verified = False
        message_encoded = encode_defunct(text=formatted_message)
        extracted_address: str = Web3().eth.account.recover_message(
            message_encoded,
            signature=signature
        )
        if extracted_address.lower() == address.lower():
            signature_verified = True
        return signature_verified, extracted_address

    @staticmethod
    def match_ethereum_signature_eip712(
        address: str,
        formatted_message: dict,
        signature: str
    ) -> tuple[bool, str]:
        logger.info("Ethereum Signature Comparison EIP-712")
        signature_verified = False
        extracted_address: str = Web3().eth.account.recover_message(
            encode_typed_data(full_message = formatted_message),
            signature = signature
        )
        if extracted_address.lower() == address.lower():
            signature_verified = True
        return signature_verified, extracted_address

    def match_cardano_signature(
        self,
        address: str,
        formatted_message: dict,
        signature: str,
        key: str
    ) -> tuple[bool, str]:
        logger.info("Cardano Signature Comparison")
        signature_verified = False
        extracted_address = self.cardano_extract_address_from_signature(formatted_message, signature, key)
        if extracted_address and extracted_address.lower() == address.lower():
            signature_verified = True
        return signature_verified, extracted_address

    def cardano_extract_address_from_signature(self, formatted_message, signature, key) -> str | None:
        signed_message = {"signature": signature, "key": key}
        verified_data = cip8.verify(signed_message)
        user_message = verified_data.get('message')
        signing_address = str(verified_data.get('signing_address'))
        return signing_address if user_message == formatted_message else None

    @staticmethod
    def trim_prefix_from_string_message(prefix: str, message: str) -> str:
        if message.startswith(prefix):
            message = message[len(prefix):]
        return message
