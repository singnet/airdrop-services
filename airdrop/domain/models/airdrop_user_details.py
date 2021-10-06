class AirdropUserDetails:
    def __init__(self, airdrop_id, window_id, address, registered_at):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self._address = address
        self._registered_at = registered_at

    def to_dict(self):
        return {
            "airdrop_id": self._airdrop_id,
            "airdrop_window_id": self._window_id,
            "address": self._address,
            "registered_at": self._registered_at
        }
