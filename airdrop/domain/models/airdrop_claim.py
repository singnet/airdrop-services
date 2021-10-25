class AirdropClaim:
    def __init__(self, airdrop_id, window_id, address, signature, amount, token_address):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._address = address
        self._signature = signature
        self._amount = amount
        self._token_address = token_address

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._window_id,
            "user_address": self._address,
            "signature": self._signature,
            "claimable_amount": self._amount,
            "token_address": self._token_address
        }
