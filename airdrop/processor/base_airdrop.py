from py_eth_sig_utils.signing import recover_typed_data, signature_to_v_r_s


class BaseAirdrop:
    pass

    @staticmethod
    def match_signature(address, formatted_message, signature):
        signature_verified = False
        recovered_address = recover_typed_data(formatted_message, *signature_to_v_r_s(bytes.fromhex(signature)))
        if recovered_address.lower() == address.lower():
            signature_verified = True
        return signature_verified, recovered_address

    @staticmethod
    def trim_prefix_from_string_message(prefix, message):
        # move to utils
        if message.startswith(prefix):
            message = message[len(prefix):]
        return message
