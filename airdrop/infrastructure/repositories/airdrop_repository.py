from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from airdrop.constants import AirdropClaimStatus
from airdrop.domain.factory.airdrop_factory import AirdropFactory
from airdrop.infrastructure.models import AirdropWindowTimelines, AirdropWindow, Airdrop, UserRegistration, \
    ClaimHistory, UserReward
from airdrop.infrastructure.repositories.base_repository import BaseRepository

from pydoc import locate
from airdrop.constants import PROCESSOR_PATH
from airdrop.processor.default_airdrop import DefaultAirdrop
from airdrop.processor.loyalty_airdrop import LoyaltyAirdrop
from airdrop.utils import datetime_in_utcnow


class AirdropRepository(BaseRepository):

    def update_txn_status(self, txn_hash, txn_status):
        try:
            transaction = self.session.query(ClaimHistory).filter(
                ClaimHistory.transaction_hash == txn_hash).first()

            if transaction is not None and txn_status == AirdropClaimStatus.SUCCESS.value:
                transaction.claimed_on = datetime_in_utcnow()

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
                .order_by(ClaimHistory.id.asc())
                .limit(5)
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
            ).join(AirdropWindow,
                   ClaimHistory.airdrop_window_id == AirdropWindow.id).filter(
                ClaimHistory.airdrop_id == airdrop_id).filter(ClaimHistory.address == address). \
                filter(UserRegistration.address == address).order_by(ClaimHistory.row_updated.desc()).all()
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
                    transaction.claimed_on = datetime_in_utcnow()
                transaction.transaction_status = txn_status
                return self.session.commit()
            else:
                claim_history = ClaimHistory(
                    address=user_address, airdrop_window_id=airdrop_window_id, airdrop_id=airdrop_id,
                    transaction_status=txn_status, transaction_hash=txn_hash, claimable_amount=amount,
                    unclaimed_amount=0)
                self.session.commit()
                return self.add(claim_history)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def airdrop_window_claim_txn(self, airdrop_id, airdrop_window_id, address, txn_hash, amount, blockchain_method):
        try:

            registered_address = self.session.query(UserRegistration).join(
                AirdropWindow, UserRegistration.airdrop_window_id == AirdropWindow.id).filter(
                UserRegistration.address == address).filter(AirdropWindow.airdrop_id == airdrop_id).filter(
                UserRegistration.airdrop_window_id == airdrop_window_id).first()

            if registered_address is None:
                raise Exception(f"Address {address} wasn't found in the list of registered addresses")

            transaction = self.session.query(ClaimHistory).filter(
                ClaimHistory.transaction_hash == txn_hash).first()

            if transaction is not None and transaction.transaction_hash == txn_hash:
                raise Exception('Transaction has been saved already')

            has_pending_or_success_txn = self.session.query(ClaimHistory).filter(
                ClaimHistory.address == address).filter(
                ClaimHistory.airdrop_window_id == airdrop_window_id).filter(
                ClaimHistory.airdrop_id == airdrop_id).filter(
                ClaimHistory.transaction_status != AirdropClaimStatus.FAILED.value).first()

            if has_pending_or_success_txn is not None:
                status_of_txn = has_pending_or_success_txn.transaction_status
                if status_of_txn == AirdropClaimStatus.SUCCESS.value:
                    raise Exception('Airdrop claimed for this window')
                else:
                    raise Exception('There is already a pending transaction')

            txn_status = AirdropClaimStatus.PENDING.value
            claim_history = ClaimHistory(
                address=address, airdrop_window_id=airdrop_window_id, airdrop_id=airdrop_id,
                transaction_status=txn_status, transaction_hash=txn_hash, claimable_amount=amount, unclaimed_amount=0,
                blockchain_method=blockchain_method)
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

    def register_airdrop(self, token_address, org_name, token_name, token_type, contract_address, portal_link,
                         documentation_link, description, github_link_for_contract):
        airdrop = Airdrop(
            token_address=token_address, org_name=org_name, token_name=token_name, contract_address=contract_address,
            portal_link=portal_link, documentation_link=documentation_link, description=description,
            github_link_for_contract=github_link_for_contract, token_type=token_type)
        self.add(airdrop)
        return self.session.query(Airdrop).filter_by(contract_address=contract_address).first()

    def register_airdrop_window(self, airdrop_id, airdrop_window_name, description, registration_required,
                                registration_start_period, registration_end_period, snapshot_required,
                                claim_start_period, claim_end_period, total_airdrop_tokens):
        airdrop_window = AirdropWindow(airdrop_id=airdrop_id, airdrop_window_name=airdrop_window_name,
                                       description=description, registration_required=registration_required,
                                       registration_start_period=registration_start_period,
                                       registration_end_period=registration_end_period,
                                       snapshot_required=snapshot_required, claim_start_period=claim_start_period,
                                       claim_end_period=claim_end_period, total_airdrop_tokens=total_airdrop_tokens)
        self.add(airdrop_window)
        return self.session.query(AirdropWindow).filter_by(airdrop_id=airdrop_id,
                                                           airdrop_window_name=airdrop_window_name).first()

    def register_airdrop_window_timeline(self, airdrop_window_id, title, description, date):
        airdrop_window_timeline = AirdropWindowTimelines(
            airdrop_window_id=airdrop_window_id, title=title, description=description, date=date)
        return self.add(airdrop_window_timeline)

    def register_user_rewards(self, airdrop_id, airdrop_window_id, rewards, address, score, normalized_score):
        user_reward = UserReward(
            airdrop_id=airdrop_id, airdrop_window_id=airdrop_window_id, address=address, rewards_awarded=rewards,
            score=score,
            normalized_score=normalized_score)
        return self.add(user_reward)

    def register_user_registration(self, airdrop_window_id, address):
        user_registration = UserRegistration(airdrop_window_id=airdrop_window_id, address=address)
        return self.add(user_registration)

    def register_claim_history(self, airdrop_id, airdrop_window_id, address, claimable_amount, unclaimable_amount,
                               transaction_status, transaction_hash):
        user_reward = ClaimHistory(
            airdrop_id=airdrop_id, airdrop_window_id=airdrop_window_id, address=address,
            claimable_amount=claimable_amount, unclaimed_amount=unclaimable_amount,
            transaction_status=transaction_status, transaction_hash=transaction_hash)
        return self.add(user_reward)

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
        return airdrop.staking_contract_address, airdrop.token_name

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
        total_eligibility_amount = self.fetch_total_eligibility_amount(airdrop_id, user_wallet_address)
        total_rewards = self.fetch_total_rewards_amount(airdrop_id, user_wallet_address)

        return total_rewards, user_wallet_address, contract_address, token_address, staking_contract_address, total_eligibility_amount

    def fetch_total_rewards_amount(self, airdrop_id, address):
        in_progress_or_completed_tx_statuses = (
            AirdropClaimStatus.SUCCESS.value, AirdropClaimStatus.PENDING.value,
            AirdropClaimStatus.CLAIM_INITIATED.value, AirdropClaimStatus.CLAIM_SUBMITTED.value,
            AirdropClaimStatus.CLAIM_FAILED.value
        )
        tokens_claim_blockchain_methods = ("token_transfer",)
        try:
            # return zero if there are no rewards, please note that MYSQL smartly sums up varchar columns and returns
            # it as a bigint if you have a very big number stored as a varchar in the rewards table.

            # Fix for the Loyalty Airdrop rewards (sum all unclaimed windows, not just those after the last one claimed)
            # Original query is in the else block
            # TODO: make more universal query for fetching total rewards amount
            airdrop = self.get_airdrop_details(airdrop_id)
            airdrop_class_path = f"{PROCESSOR_PATH}.{airdrop.airdrop_processor}"
            airdrop_class = locate(airdrop_class_path) if airdrop.airdrop_processor else DefaultAirdrop

            if airdrop_class is LoyaltyAirdrop:
                query_rewards = text(
                    "SELECT IFNULL( SUM(ur.rewards_awarded),0) AS 'total_rewards' FROM user_rewards ur, airdrop_window aw "
                    "WHERE ur.airdrop_window_id = aw.row_id AND ur.address = :address AND aw.airdrop_id = :airdrop_id "
                    "AND aw.claim_start_period <= current_timestamp  AND exists (SELECT 1 FROM airdrop_window WHERE "
                    "current_timestamp <= claim_end_period  AND airdrop_id = :airdrop_id AND "
                    "claim_start_period <= current_timestamp) AND ur.airdrop_window_id IN "
                    "( SELECT airdrop_window_id FROM user_registrations WHERE address = :address AND "
                    "airdrop_window_id IN (SELECT row_id FROM airdrop_window WHERE airdrop_id = :airdrop_id));"
                )
                result_rewards = self.session.execute(query_rewards, {
                    "address": address, "airdrop_id": airdrop_id
                })
                query_claimed = text(
                    "SELECT IFNULL(SUM(claimable_amount),0) AS 'total_claimed' FROM claim_history ch WHERE "
                    "ch.address = :address AND ch.airdrop_id = :airdrop_id AND ch.blockchain_method IN "
                    ":tokens_claim_blockchain_methods AND ch.transaction_status IN :in_progress_or_completed_tx_statuses"
                )
                result_claimed = self.session.execute(query_claimed, {
                    "address": address, "airdrop_id": airdrop_id,
                    "tokens_claim_blockchain_methods": tokens_claim_blockchain_methods,
                    "in_progress_or_completed_tx_statuses": in_progress_or_completed_tx_statuses
                })
                row_rewards = result_rewards.mappings().first()
                full_rewards = int(row_rewards["total_rewards"]) if row_rewards else 0
                row_claimed = result_claimed.mappings().first()
                claimed_rewards = int(row_claimed["total_claimed"]) if row_claimed else 0
                total_rewards = full_rewards - claimed_rewards
            else:
                query = text(
                    "SELECT IFNULL( SUM(ur.rewards_awarded),0) AS 'total_rewards' FROM user_rewards ur, airdrop_window aw "
                    "WHERE ur.airdrop_window_id = aw.row_id AND ur.address = :address AND aw.airdrop_id = :airdrop_id "
                    "AND aw.claim_start_period <= current_timestamp  AND exists (SELECT 1 FROM airdrop_window WHERE "
                    "current_timestamp <= claim_end_period  AND airdrop_id = :airdrop_id AND "
                    "claim_start_period <= current_timestamp) AND ur.airdrop_window_id > "
                    "(SELECT IFNULL (MAX(airdrop_window_id), -1) FROM claim_history ch WHERE ch.address = :address "
                    "AND ch.transaction_status IN :in_progress_or_completed_tx_statuses AND ch.airdrop_id = :airdrop_id) "
                    "AND ur.airdrop_window_id IN ( SELECT airdrop_window_id FROM user_registrations  "
                    "WHERE address = :address AND airdrop_window_id IN (SELECT row_id FROM airdrop_window "
                    "WHERE airdrop_id = :airdrop_id));"
                )
                result = self.session.execute(query, {
                    "address": address, "airdrop_id": airdrop_id,
                    "in_progress_or_completed_tx_statuses": in_progress_or_completed_tx_statuses
                })
                row = result.mappings().first()
                total_rewards = int(row["total_rewards"]) if row else 0
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
        # determine the final result here, this was the service layer does not have to deal
        # with extracting "total_rewards" from the o/p sent

        return total_rewards

    def fetch_total_eligibility_amount(self, airdrop_id, address):
        try:
            # return zero if there are no rewards, please note that MYSQL smartly sums up varchar columns and returns
            # it as a bigint if you have a very big number stored as a varchar in the rewards table.
            query = text(
                "SELECT IFNULL( sum(ur.rewards_awarded),0) AS 'total_eligibility_rewards' FROM user_rewards ur, "
                "airdrop_window aw WHERE ur.airdrop_window_id = aw.row_id AND ur.address = :address "
                "AND aw.airdrop_id = :airdrop_id AND aw.claim_start_period <= current_timestamp "
                "AND exists (SELECT 1 FROM airdrop_window WHERE current_timestamp <= claim_end_period "
                "AND airdrop_id = :airdrop_id AND claim_start_period <= current_timestamp )  "
                "AND ur.airdrop_window_id IN ( SELECT airdrop_window_id FROM user_registrations "
                "WHERE address = :address AND airdrop_window_id IN (SELECT row_id FROM airdrop_window "
                "WHERE airdrop_id = :airdrop_id));"
            )
            result = self.session.execute(
                query, {'address': address, 'airdrop_id': airdrop_id})
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
        # value_retrieved = result.fetchall()[0]
        # total_eligible_rewards = value_retrieved[0]
        value_retrieved = result.mappings().first()
        total_eligible_rewards = int(value_retrieved["total_eligibility_rewards"]) if value_retrieved else 0
        return int(total_eligible_rewards)

    def get_airdrops_schedule(self, airdrop_id):
        try:
            airdrop_row_data = (
                self.session.query(Airdrop)
                .join(
                    AirdropWindow,
                    Airdrop.id == AirdropWindow.airdrop_id,
                    isouter = True
                )
                .join(
                    AirdropWindowTimelines,
                    AirdropWindow.id == AirdropWindowTimelines.airdrop_window_id,
                    isouter = True
                )
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

    def get_airdrop_details(self, airdrop_id):
        return self.session.query(Airdrop).filter(Airdrop.id == airdrop_id).first()

    def get_airdrop_window_details(self, airdrop_window_id):
        return self.session.query(AirdropWindow).filter(AirdropWindow.id == airdrop_window_id).first()

    def update_minimum_stake_amount(self, airdrop_window_id, minimum_stake_amount):
        try:
            transaction = self.session.query(AirdropWindow).filter(
                AirdropWindow.id == airdrop_window_id).first()
            if transaction is not None:
                transaction.minimum_stake_amount = minimum_stake_amount
                return self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
