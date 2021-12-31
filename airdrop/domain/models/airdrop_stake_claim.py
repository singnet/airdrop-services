class AirdropStakeClaim:
    def __init__(self, airdrop_id, window_id, address, claimable_tokens_to_wallet, stakable_tokens, is_stakable, stakable_token_name, airdrop_rewards):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._address = address
        self._claimable_tokens_to_wallet = claimable_tokens_to_wallet
        self._stakable_tokens = stakable_tokens
        self._is_stakable = is_stakable
        self._stakable_token_name = stakable_token_name,
        self._airdrop_rewards = airdrop_rewards

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._window_id,
            "address": self._address,
            "claimable_tokens_to_wallet": self._claimable_tokens_to_wallet,
            "stakable_tokens": self._stakable_tokens,
            "is_stakable": self._is_stakable,
            "stakable_token_name": self._stakable_token_name,
            "airdrop_rewards": self._airdrop_rewards
        }
