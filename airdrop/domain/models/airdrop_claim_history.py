class AirdropClaimHistory:
    def __init__(self, airdrop_id, airdrop_window_id, address, txn_status, txn_hash, claimable_amount):
        self._airdrop_id = airdrop_id
        self._airdrop_window_id = airdrop_window_id
        self._address = address
        self._txn_status = txn_status
        self._txn_hash = txn_hash
        self._claimable_amount = claimable_amount

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._airdrop_window_id,
            "user_address": self._address,
            "txn_hash": self._txn_hash,
            "txn_status": self._txn_status,
            "claimable_amount": self._claimable_amount,
        }
