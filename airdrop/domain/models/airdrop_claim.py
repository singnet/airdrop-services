class AirdropClaim:
    def __init__(self, airdrop_id, window_id, address, signature, amount, token_address, contract_address, staking_contract_address,total_eligibility_amount):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._address = address
        self._signature = signature
        self._amount = amount
        self._token_address = token_address
        self._contract_address = contract_address
        self._staking_contract_address = staking_contract_address
        self._total_eligibility_amount = total_eligibility_amount

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._window_id,
            "user_address": self._address,
            "signature": self._signature,
            "claimable_amount": str(self._amount),
            "token_address": self._token_address,
            "contract_address": self._contract_address,
            "staking_contract_address": self._staking_contract_address,
            "total_eligibility_amount": str(self._total_eligibility_amount)
        }
