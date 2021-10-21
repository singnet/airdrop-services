from sqlalchemy.exc import SQLAlchemyError

from airdrop.infrastructure.repositories.base_repository import BaseRepository
from airdrop.infrastructure.models import AirdropWindowTimelines, AirdropWindow, Airdrop, UserBalanceSnapshot, UserRegistration, ClaimHistory, AirdropWindowEligibilityRule
from airdrop.domain.factory.airdrop_factory import AirdropFactory
from datetime import datetime
from airdrop.constants import AirdropClaimStatus


class AirdropRepository(BaseRepository):

    def airdrop_window_claim_history(self, airdrop_id, airdrop_window_id, address):
        try:
            claim_raw_data = self.session.query(ClaimHistory).filter(
                ClaimHistory.airdrop_window_id == airdrop_window_id).filter(ClaimHistory.airdrop_id == airdrop_id).filter(ClaimHistory.address == address).all()
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

    def airdrop_window_claim_txn(self, airdrop_id, airdrop_window_id, address, txn_hash, txn_status, amount):
        try:
            is_existing_txn_hash = self.session.query(ClaimHistory).filter(
                ClaimHistory.transaction_hash == txn_hash).first()

            if is_existing_txn_hash is not None:
                raise Exception('Duplicate Txn hash')

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
                .filter(ClaimHistory.transaction_status != AirdropClaimStatus.FAILED)
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
        return self.add(airdrop)

    def register_airdrop_window(self, airdrop_id, airdrop_window_name, description, registration_required, registration_start_period, registration_end_period, snapshot_required, claim_start_period, claim_end_period):
        airdrop_window = AirdropWindow(airdrop_id=airdrop_id, airdrop_window_name=airdrop_window_name, description=description, registration_required=registration_required, registration_start_period=registration_start_period,
                                       registration_end_period=registration_end_period, snapshot_required=snapshot_required, claim_start_period=claim_start_period, claim_end_period=claim_end_period)
        return self.add(airdrop_window)

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
                .filter(UserRegistration.is_eligible == True)
                .filter(AirdropWindow.airdrop_id == airdrop_id)
                .filter(AirdropWindow.id == airdrop_window_id)
                .filter(AirdropWindow.claim_start_period <= date_time)
                .filter(AirdropWindow.claim_end_period >= date_time)
                .first()
            )

            if is_eligible_user is None:
                raise Exception('Non eligible user')

            balance_raw_data = self.session.query(UserBalanceSnapshot).filter(UserBalanceSnapshot.address == address).filter(
                UserBalanceSnapshot.airdrop_window_id == airdrop_window_id).first()

            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        if balance_raw_data is not None:
            return balance_raw_data.balance
        else:
            return 0

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
        raise Exception("Invalid token name")
