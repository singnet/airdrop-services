class AirdropWindowEligibility:
    def __init__(self, airdrop_id, airdrop_window_id, address, is_eligible_user, is_already_registered, is_airdrop_window_claimed, airdrop_claim_status, reject_reason, rewards_awards):
        self._is_eligible_user = is_eligible_user
        self._is_already_registered = is_already_registered
        self._is_airdrop_window_claimed = is_airdrop_window_claimed
        self._airdrop_claim_status = airdrop_claim_status
        self._address = address
        self._airdrop_id = airdrop_id
        self._airdrop_window_id = airdrop_window_id
        self._reject_reason = reject_reason
        self._rewards_awards = rewards_awards

    def to_dict(self):
        return {
            "is_eligible": self._is_eligible_user,
            "is_already_registered":  self._is_already_registered,
            "is_airdrop_window_claimed":  self._is_airdrop_window_claimed,
            "airdrop_window_claim_status":  self._airdrop_claim_status,
            "user_address": self._address,
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._airdrop_window_id,
            "reject_reason": self._reject_reason,
            "airdrop_window_rewards": self._rewards_awards
        }
