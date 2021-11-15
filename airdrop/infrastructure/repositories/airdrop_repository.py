from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.repositories.base_repository import BaseRepository
from airdrop.infrastructure.models import AirdropWindowTimelines, AirdropWindow, Airdrop, UserRegistration, ClaimHistory, UserReward
from airdrop.domain.factory.airdrop_factory import AirdropFactory
from datetime import datetime
from airdrop.constants import AirdropClaimStatus


class AirdropRepository(BaseRepository):

    def update_txn_status(self, txn_hash, txn_status):
        try:
            transaction = self.session.query(ClaimHistory).filter(
                ClaimHistory.transaction_hash == txn_hash).first()

            if transaction is not None and txn_status == AirdropClaimStatus.SUCCESS.value:
                transaction.claimed_on = datetime.utcnow()

            if transaction is not None:
                transaction.transaction_status = txn_status
                return self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def get_pending_txns(self):
        try:
            pending_txns = (
                self.session.query(ClaimHistory)
                .filter(ClaimHistory.transaction_status == AirdropClaimStatus.PENDING.value)
                .all()
            )
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        return pending_txns

    def airdrop_window_claim_history(self, airdrop_id, address):
        try:
            claim_raw_data = self.session.query(ClaimHistory).join(
                UserRegistration,
                ClaimHistory.airdrop_window_id == UserRegistration.airdrop_window_id
            ).filter(
                ClaimHistory.airdrop_id == airdrop_id).filter(ClaimHistory.address == address).filter(UserRegistration.address == address).all()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        claim_history = []
        if claim_raw_data is not None:
            claim_history = [
                AirdropFactory.convert_claim_history_model_to_entity_model(
                    claim)
                for claim in claim_raw_data
            ]

        return claim_history

    def create_or_update_txn(self, airdrop_id, airdrop_window_id, user_address, txn_hash, txn_status, amount):
        try:

            transaction = self.session.query(ClaimHistory).filter(
                ClaimHistory.transaction_hash == txn_hash).first()

            if transaction is not None:
                existing_txn_hash = transaction.transaction_hash
                if existing_txn_hash != txn_hash:
                    transaction.transaction_hash = txn_hash
                if txn_status == AirdropClaimStatus.SUCCESS.value:
                    transaction.claimed_on = datetime.utcnow()
                transaction.transaction_status = txn_status
                return self.session.commit()
            else:
                claim_history = ClaimHistory(
                    address=user_address, airdrop_window_id=airdrop_window_id, airdrop_id=airdrop_id, transaction_status=txn_status, transaction_hash=txn_hash, claimable_amount=amount, unclaimed_amount=0)
                self.session.commit()
                return self.add(claim_history)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def airdrop_window_claim_txn(self, airdrop_id, airdrop_window_id, address, txn_hash, amount):
        try:

            is_valid_address = self.session.query(UserRegistration).filter(
                UserRegistration.address == address).filter(AirdropWindow.airdrop_id == airdrop_id).filter(UserRegistration.airdrop_window_id == airdrop_window_id).first()

            if is_valid_address is None:
                raise Exception('Invalid address')

            transaction = self.session.query(ClaimHistory).filter(
                ClaimHistory.transaction_hash == txn_hash).first()

            if transaction is not None and transaction.transaction_hash == txn_hash:
                raise Exception('Transaction has been saved already')

            has_pending_or_success_txn = self.session.query(ClaimHistory).filter(ClaimHistory.address == address).filter(
                ClaimHistory.airdrop_window_id == airdrop_window_id).filter(ClaimHistory.airdrop_id == airdrop_id).filter(ClaimHistory.transaction_status != AirdropClaimStatus.FAILED.value).first()

            if has_pending_or_success_txn is not None:
                status_of_txn = has_pending_or_success_txn.transaction_status
                if status_of_txn == AirdropClaimStatus.SUCCESS.value:
                    raise Exception('Airdrop claimed for this window')
                else:
                    raise Exception('There is already a pending transaction')

            txn_status = AirdropClaimStatus.PENDING.value
            claim_history = ClaimHistory(
                address=address, airdrop_window_id=airdrop_window_id, airdrop_id=airdrop_id, transaction_status=txn_status, transaction_hash=txn_hash, claimable_amount=amount, unclaimed_amount=0)
            self.session.commit()
            return self.add(claim_history)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def is_claimed_airdrop_window(self, address, airdrop_window_id):
        try:
            is_claimed_address = (
                self.session.query(ClaimHistory)
                .filter(ClaimHistory.airdrop_window_id == airdrop_window_id)
                .filter(ClaimHistory.address == address)
                .filter(ClaimHistory.transaction_status != AirdropClaimStatus.FAILED.value)
                .first()
            )

            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        if is_claimed_address is not None:
            raise Exception('Airdrop Already claimed / pending')

    def register_airdrop(self, address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link_for_contract):
        airdrop = Airdrop(
            address=address, org_name=org_name, token_name=token_name, contract_address=contract_address, portal_link=portal_link, documentation_link=documentation_link, description=description, github_link_for_contract=github_link_for_contract, token_type=token_type)
        self.add(airdrop)
        return self.session.query(Airdrop).filter_by(address=address).first()

    def register_airdrop_window(self, airdrop_id, airdrop_window_name, description, registration_required, registration_start_period, registration_end_period, snapshot_required, claim_start_period, claim_end_period, total_airdrop_tokens):
        airdrop_window = AirdropWindow(airdrop_id=airdrop_id, airdrop_window_name=airdrop_window_name, description=description, registration_required=registration_required, registration_start_period=registration_start_period,
                                       registration_end_period=registration_end_period, snapshot_required=snapshot_required, claim_start_period=claim_start_period, claim_end_period=claim_end_period, total_airdrop_tokens=total_airdrop_tokens)
        return self.add(airdrop_window)

    def register_airdrop_window_timeline(self, airdrop_window_id, title, description, date):
        airdrop_window_timeline = AirdropWindowTimelines(
            airdrop_window_id=airdrop_window_id, title=title, description=description, date=date)
        return self.add(airdrop_window_timeline)

    def get_token_address(self, airdrop_id):
        airdrop = self.session.query(Airdrop).filter_by(id=airdrop_id).first()

        if airdrop is None:
            raise Exception("Airdrop not found")

        return airdrop.contract_address

    def get_airdrop_window_claimable_amount(self, airdrop_id, airdrop_window_id, address):
        try:
            date_time = datetime.utcnow()
            is_eligible_user = (
                self.session.query(UserRegistration, AirdropWindow)
                .join(
                    AirdropWindow,
                    AirdropWindow.id == UserRegistration.airdrop_window_id
                )
                .filter(UserRegistration.address == address)
                .filter(AirdropWindow.airdrop_id == airdrop_id)
                .filter(AirdropWindow.id == airdrop_window_id)
                .filter(AirdropWindow.claim_start_period <= date_time)
                .filter(AirdropWindow.claim_end_period >= date_time)
                .first()
            )

            if is_eligible_user is None:
                raise Exception('Non eligible user')

            balance_raw_data = self.session.query(UserReward).filter(UserReward.address == address).filter(
                UserReward.airdrop_window_id == airdrop_window_id).filter(UserReward.airdrop_id == airdrop_id).first()

            airdrop_row_data = self.session.query(
                Airdrop.address).filter(Airdrop.id == airdrop_id).first()

            token_address = airdrop_row_data.address

            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        if balance_raw_data is not None:
            return balance_raw_data.rewards_awarded, token_address
        else:
            return 0, token_address

    def get_airdrops(self, limit, skip):
        try:

            airdrop_window_data = (
                self.session.query(AirdropWindow)
                .limit(limit)
                .offset(skip)
                .all()
            )
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        airdrop_windows = []
        if airdrop_window_data is not None:
            airdrop_windows = [
                AirdropFactory.convert_airdrop_window_model_to_entity_model(
                    window)
                for window in airdrop_window_data
            ]
        return airdrop_windows

    def get_airdrops_schedule(self, token_address):
        try:
            airdrop_row_data = (
                self.session.query(Airdrop)
                .join(
                    AirdropWindow,
                    Airdrop.id == AirdropWindow.airdrop_id,
                )
                .join(AirdropWindowTimelines, AirdropWindow.id == AirdropWindowTimelines.airdrop_window_id)
                .filter(Airdrop.address == token_address)
                .first()
            )
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        if airdrop_row_data is not None:
            return AirdropFactory.convert_airdrop_schedule_model_to_entity_model(
                airdrop_row_data)
        raise Exception("Invalid token address")
