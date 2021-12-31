from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

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

    def airdrop_window_claim_txn(self, airdrop_id, airdrop_window_id, address, txn_hash, amount, blockchain_method):
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
                address=address, airdrop_window_id=airdrop_window_id, airdrop_id=airdrop_id, transaction_status=txn_status, transaction_hash=txn_hash, claimable_amount=amount, unclaimed_amount=0, blockchain_method=blockchain_method)
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

    def register_airdrop(self, token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link_for_contract, stakable_token_name):
        airdrop = Airdrop(
            token_address=token_address, org_name=org_name, token_name=token_name, contract_address=contract_address, portal_link=portal_link, documentation_link=documentation_link, description=description, github_link_for_contract=github_link_for_contract, token_type=token_type, stakable_token_name=stakable_token_name)
        self.add(airdrop)
        return self.session.query(Airdrop).filter_by(token_address=token_address).first()

    def register_airdrop_window(self, airdrop_id, airdrop_window_name, description, registration_required, registration_start_period, registration_end_period, snapshot_required, claim_start_period, claim_end_period, total_airdrop_tokens):
        airdrop_window = AirdropWindow(airdrop_id=airdrop_id, airdrop_window_name=airdrop_window_name, description=description, registration_required=registration_required, registration_start_period=registration_start_period,
                                       registration_end_period=registration_end_period, snapshot_required=snapshot_required, claim_start_period=claim_start_period, claim_end_period=claim_end_period, total_airdrop_tokens=total_airdrop_tokens)
        return self.add(airdrop_window)

    def register_airdrop_window_timeline(self, airdrop_window_id, title, description, date):
        airdrop_window_timeline = AirdropWindowTimelines(
            airdrop_window_id=airdrop_window_id, title=title, description=description, date=date)
        return self.add(airdrop_window_timeline)

    def get_contract_address(self, airdrop_id):
        try:
            airdrop = self.session.query(
                Airdrop).filter_by(id=airdrop_id).first()
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        if airdrop is None:
            raise Exception('Airdrop not found')
        return airdrop.contract_address

    def get_token_address(self, airdrop_id):
        try:
            airdrop = self.session.query(
                Airdrop).filter_by(id=airdrop_id).first()
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        if airdrop is None:
            raise Exception("Airdrop not found")

        return airdrop.token_address

    def get_staking_contract_address(self, airdrop_id):
        try:
            airdrop = self.session.query(
                Airdrop).filter_by(id=airdrop_id).first()
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        if airdrop is None:
            raise Exception("Airdrop not found")
        return airdrop.staking_contract_address, airdrop.stakable_token_name

    def get_airdrop_window_claimable_info(self, airdrop_id, airdrop_window_id, user_wallet_address):
        try:
            airdrop = (
                self.session.query(Airdrop)
                .filter(Airdrop.id == airdrop_id)
                .first()
            )

            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        if airdrop is None:
            raise Exception('Invalid Airdrop')

        total_rewards = 0
        contract_address = airdrop.contract_address
        token_address = airdrop.token_address
        staking_contract_address = airdrop.staking_contract_address

        balance_raw_data = self.fetch_total_rewards_amount(
            airdrop_id, user_wallet_address)

        if len(balance_raw_data) > 0:
            balance_data = balance_raw_data[0]
            total_rewards = str(
                balance_data['total_rewards']) if balance_data['total_rewards'] is not None else 0

        return total_rewards, user_wallet_address, contract_address, token_address, staking_contract_address

    def fetch_total_rewards_amount(self, airdrop_id, address):
        try:
            query = text("select sum(ur.rewards_awarded) AS 'total_rewards' FROM user_rewards ur, airdrop_window aw where ur.airdrop_window_id = aw.row_id and ur.address = :address and aw.airdrop_id = :airdrop_id and aw.claim_start_period <= current_timestamp and ur.airdrop_window_id not in (select airdrop_window_id from claim_history where address = :address and transaction_status in ('SUCCESS', 'PENDING')) and ur.airdrop_window_id > (select ifnull (max(airdrop_window_id), -1) from claim_history where address = :address and transaction_status in ('SUCCESS', 'PENDING'));")
            result = self.session.execute(
                query, {'address': address, 'airdrop_id': airdrop_id})
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
        return result.fetchall()

    def get_airdrops_schedule(self, airdrop_id):
        try:
            airdrop_row_data = (
                self.session.query(Airdrop)
                .join(
                    AirdropWindow,
                    Airdrop.id == AirdropWindow.airdrop_id,
                )
                .join(AirdropWindowTimelines, AirdropWindow.id == AirdropWindowTimelines.airdrop_window_id)
                .filter(Airdrop.id == airdrop_id)
                .first()
            )
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
        if airdrop_row_data is not None:
            return AirdropFactory.convert_airdrop_schedule_model_to_entity_model(airdrop_row_data)
        else:
            raise Exception('Non eligible user')
