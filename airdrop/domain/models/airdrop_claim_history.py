class AirdropClaimHistory:
    def __init__(self, airdrop_id, airdrop_window_id, address, txn_status, txn_hash, claimable_amount, claimed_on, user_registration):
        self._airdrop_id = airdrop_id
        self._airdrop_window_id = airdrop_window_id
        self._address = address
        self._txn_status = txn_status
        self._txn_hash = txn_hash
        self._claimable_amount = claimable_amount
        self._claimed_on = claimed_on
        self._user_registration = user_registration[0]

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._airdrop_window_id,
            "user_address": self._address,
            "txn_hash": self._txn_hash,
            "txn_status": self._txn_status,
            "claimable_amount": self._claimable_amount,
            "claimed_on": self._claimed_on,
            "registered_at": str(self._user_registration.registered_at),
            "is_eligible": self._user_registration.is_eligible
        }
