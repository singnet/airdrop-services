from datetime import datetime, timezone

import cbor2
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from eth_account.messages import encode_defunct, encode_typed_data
from web3 import Web3

from common.logger import get_logger

logger = get_logger(__name__)


def datetime_in_utcnow():
    return datetime.now(timezone.utc)


class Utils:

    @staticmethod
    def match_ethereum_signature_eip191(
        address: str,
        message: str,
        signature: str
    ) -> bool:
        logger.info("Ethereum Signature Comparison EIP-191")
        signature_verified = False
        message_encoded = encode_defunct(text=message)
        extracted_address: str = Web3().eth.account.recover_message(
            message_encoded,
            signature=signature
        )
        if extracted_address.lower() == address.lower():
            signature_verified = True
        return signature_verified

    @staticmethod
    def match_ethereum_signature_eip712(
        address: str,
        message: dict,
        signature: str
    ) -> tuple[bool, str]:
        logger.info("Ethereum Signature Comparison EIP-712")
        signature_verified = False
        extracted_address: str = Web3().eth.account.recover_message(
            encode_typed_data(full_message = message),
            signature = signature
        )
        if extracted_address.lower() == address.lower():
            signature_verified = True
        return signature_verified, extracted_address

    def match_cardano_signature(
        self,
        message_hex: str,
        signature_hex: str,
        key_hex: str
    ) -> bool:
        logger.info("Cardano Signature Comparison")
        try:
            message = message_hex.encode('UTF-8')
            key_cbor = bytes.fromhex(key_hex)
            key_data = cbor2.loads(key_cbor)
            public_key_bytes = key_data[-2]
            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

            signature_cbor = bytes.fromhex(signature_hex)
            signature_data = cbor2.loads(signature_cbor)

            body_protected = signature_data[0]
            signature = signature_data[3]
            is_hashed = False
            content_to_sign = None

            if 'hashed' in signature_data[1]:
                is_hashed = signature_data[1]['hashed']
            if is_hashed:
                content_to_sign = signature_data[2]
            else:
                content_to_sign = message
            
            sig_structure = ["Signature1", body_protected,
                            b"", content_to_sign]

            sig_structure_cbor = cbor2.dumps(sig_structure)
            public_key.verify(signature, sig_structure_cbor)
            logger.info(f"Cardano signature verified successfully")
            return True
        except Exception as e:
            logger.exception(f"Exception: {str(e)}")
            raise e

    @staticmethod
    def trim_prefix_from_string_message(prefix: str, message: str) -> str:
        if message.startswith(prefix):
            message = message[len(prefix):]
        return message
