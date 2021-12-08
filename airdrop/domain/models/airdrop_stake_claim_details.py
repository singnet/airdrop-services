class AirdropStakeClaimDetails:
    def __init__(self, airdrop_id, window_id, claimable_amount,stake_amount, stake_window_is_open, stake_window_start_time,stake_window_end_time):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._claimable_amount = claimable_amount
        self._stake_window_is_open = stake_window_is_open
        self._stake_window_start_time = stake_window_start_time
        self._stake_window_end_time = stake_window_end_time
        self._stake_amount = stake_amount

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._window_id,
            "claimable_amount": self._claimable_amount,
            "stake_amount": self._stake_amount,
            "is_stake_window_is_open": self._stake_window_is_open,
            "stake_window_start_time": self._stake_window_start_time,
            "stake_window_end_time": self._stake_window_end_time
        }
