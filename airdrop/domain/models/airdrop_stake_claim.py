class AirdropStakeClaim:
    def __init__(self, airdrop_id, window_id, address, claimable_tokens_to_wallet, stakable_tokens, is_stakable, token_name, airdrop_rewards,total_eligible_amount):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._address = address
        self._claimable_tokens_to_wallet = claimable_tokens_to_wallet
        self._stakable_tokens = stakable_tokens
        self._is_stakable = is_stakable
        self._token_name = token_name
        self._airdrop_rewards = airdrop_rewards
        self._total_eligible_amount = total_eligible_amount

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._window_id,
            "address": self._address,
            "claimable_tokens_to_wallet": str(self._claimable_tokens_to_wallet),
            "stakable_tokens": str(self._stakable_tokens),
            "is_stakable": self._is_stakable,
            "token_name": self._token_name,
            "airdrop_rewards": str(self._airdrop_rewards),
            "total_eligible_amount":str(self._total_eligible_amount)
        }
