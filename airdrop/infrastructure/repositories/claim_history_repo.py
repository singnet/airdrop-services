from sqlalchemy.exc import SQLAlchemyError

from airdrop.constants import AirdropClaimStatus
from airdrop.infrastructure.models import ClaimHistory
from airdrop.infrastructure.repositories.base_repository import BaseRepository


class ClaimHistoryRepository(BaseRepository):
    def add_claim(self, claim_payload):
        self.add(
            ClaimHistory(
                airdrop_id=claim_payload["airdrop_id"],
                airdrop_window_id=claim_payload["airdrop_window_id"],
                address=claim_payload["address"],
                blockchain_method=claim_payload["blockchain_method"],
                claimable_amount=claim_payload["claimable_amount"],
                unclaimed_amount=claim_payload["unclaimed_amount"],
                transaction_status=claim_payload["transaction_status"],
                claimed_on=claim_payload["claimed_on"]

            )
        )

    def get_pending_claims_for_given_airdrop_id(self, airdrop_id, blockchain_method):
        claims = self.session.query(ClaimHistory). \
            filter(ClaimHistory.airdrop_id == airdrop_id). \
            filter(ClaimHistory.blockchain_method == blockchain_method). \
            filter(ClaimHistory.transaction_status == AirdropClaimStatus.PENDING.value).all()
        return claims

    def update_claim_status(self, address, airdrop_window_id, blockchain_method, transaction_status,
                            transaction_hash=None):
        try:
            claim = self.session.query(ClaimHistory) \
                .filter(ClaimHistory.address == address, self.session.airdrop_window_id == airdrop_window_id,
                        ClaimHistory.blockchain_method == blockchain_method) \
                .first()
            if claim:
                claim.transaction_status = transaction_status
                claim.transaction_hash = transaction_hash if transaction_hash else claim.transaction_hash
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
