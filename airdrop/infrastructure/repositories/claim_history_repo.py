from airdrop.infrastructure.models import ClaimHistory
from airdrop.infrastructure.repositories.base_repository import BaseRepository


class ClaimHistoryRepository(BaseRepository):
    def add_claim(self, claim_payload):
        self.session.add(
            ClaimHistory(
                airdrop_id=claim_payload["airdrop_id"],
                airdrop_window_id=claim_payload["airdrop_window_id"],
                address=claim_payload["address"],
                blockchain_method=claim_payload["blockchain_method"],
                claimable_amount=claim_payload["claimable_amount"],
                unclaimed_amount=claim_payload["unclaimed_amount"],
                transaction_status=claim_payload["AirdropClaimStatus.PENDING.value"],
                claimed_on=claim_payload["dt.utcnow()"]

            )
        )
