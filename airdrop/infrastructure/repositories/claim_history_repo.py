from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from airdrop.constants import AirdropClaimStatus
from airdrop.infrastructure.models import ClaimHistory
from airdrop.infrastructure.repositories.base_repository import BaseRepository
from common.logger import get_logger

logger = get_logger(__name__)


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
        response = []
        try:
            query = text("SELECT ur.address, json_extract(ur.signature_details, \"$.message.Airdrop.cardanoAddress\") "
                         "AS cardano_address, ch.airdrop_window_id, ch.claimable_amount FROM user_registrations ur, "
                         "airdrop ad, airdrop_window aw, claim_history ch  WHERE ad.row_id = :airdrop_id AND "
                         "ad.row_id = aw.airdrop_id  AND aw.row_id = ur.airdrop_window_id AND "
                         "ch.airdrop_window_id = aw.row_id AND ch.transaction_status = :transaction_status AND "
                         "ch.blockchain_method = :blockchain_method AND ur.address = ch.address")
            result = self.session.execute(query, {"airdrop_id": airdrop_id, "blockchain_method": blockchain_method,
                                                  "transaction_status": AirdropClaimStatus.PENDING.value}
                                          )
            for record in result.mappings().all():
                cardano_address = record["cardano_address"].strip('\"')
                response.append({
                    "address": record["address"],
                    "cardano_address": cardano_address,
                    "airdrop_window_id": record["airdrop_window_id"],
                    "claimable_amount": int(record["claimable_amount"])
                })
            self.session.commit()
        except SQLAlchemyError as e:
            logger.exception(f"SQLAlchemyError: {str(e)}")
            self.session.rollback()
            raise e
        return response

    def update_claim_status(self, address, airdrop_window_id, blockchain_method, transaction_status,
                            transaction_hash=None, transaction_details=None):
        logger.info(f"Updating claim status for {address = }, {airdrop_window_id = }, "
                    f"{blockchain_method = } to '{transaction_status}'")
        try:
            claim = self.session.query(ClaimHistory) \
                .filter(ClaimHistory.address == address, ClaimHistory.airdrop_window_id == airdrop_window_id,
                        ClaimHistory.blockchain_method == blockchain_method) \
                .first()
            if claim:
                claim.transaction_status = transaction_status
                claim.transaction_hash = transaction_hash if transaction_hash else claim.transaction_hash
                if transaction_details:
                    claim.transaction_details = transaction_details
            self.session.commit()
        except SQLAlchemyError as e:
            logger.exception(f"SQLAlchemyError: {str(e)}")
            self.session.rollback()
            raise e

    def get_unique_transaction_hashes(self, airdrop_id=None, transaction_status=None):
        query = self.session.query(ClaimHistory.transaction_hash)
        if airdrop_id:
            query = query.filter(ClaimHistory.airdrop_id == airdrop_id)
        if transaction_status:
            query = query.filter(ClaimHistory.transaction_status == transaction_status)
        transaction_hashes_db = query.distinct().all()
        return [transaction_hash_db[0] for transaction_hash_db in transaction_hashes_db]

    def update_claim_status_for_given_transaction_hashes(self, transaction_hashes, transaction_status):
        try:
            claims = self.session.query(ClaimHistory) \
                .filter(ClaimHistory.transaction_hash.in_(transaction_hashes)) \
                .all()
            for claim in claims:
                claim.transaction_status = transaction_status
            self.session.commit()
        except SQLAlchemyError as e:
            logger.exception(f"SQLAlchemyError: {str(e)}")
            self.session.rollback()
            raise e
