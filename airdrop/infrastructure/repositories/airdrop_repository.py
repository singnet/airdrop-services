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
                ClaimHistory.airdrop_id == airdrop_id).filter(ClaimHistory.address == address).\
                filter(UserRegistration.address == address).all()
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

    def register_airdrop(self, token_address, org_name, token_name, token_type, contract_address, portal_link, documentation_link, description, github_link_for_contract):
        airdrop = Airdrop(
            token_address=token_address, org_name=org_name, token_name=token_name, contract_address=contract_address, portal_link=portal_link, documentation_link=documentation_link, description=description, github_link_for_contract=github_link_for_contract, token_type=token_type)
        self.add(airdrop)
        return self.session.query(Airdrop).filter_by(contract_address=contract_address).first()


    def register_airdrop_window(self, airdrop_id, airdrop_window_name, description, registration_required, registration_start_period, registration_end_period, snapshot_required, claim_start_period, claim_end_period, total_airdrop_tokens):
        airdrop_window = AirdropWindow(airdrop_id=airdrop_id, airdrop_window_name=airdrop_window_name, description=description, registration_required=registration_required, registration_start_period=registration_start_period,
                                       registration_end_period=registration_end_period, snapshot_required=snapshot_required, claim_start_period=claim_start_period, claim_end_period=claim_end_period, total_airdrop_tokens=total_airdrop_tokens)
        self.add(airdrop_window)
        return self.session.query(AirdropWindow).filter_by(airdrop_id=airdrop_id,
                                                           airdrop_window_name=airdrop_window_name).first()

    def register_airdrop_window_timeline(self, airdrop_window_id, title, description, date):
        airdrop_window_timeline = AirdropWindowTimelines(
            airdrop_window_id=airdrop_window_id, title=title, description=description, date=date)
        return self.add(airdrop_window_timeline)

    def register_user_rewards(self,airdrop_id, airdrop_window_id, rewards,address,score,normalized_score):
        user_reward = UserReward(
            airdrop_id=airdrop_id,airdrop_window_id=airdrop_window_id, address=address,rewards_awarded=rewards,score=score,
        normalized_score=normalized_score)
        return self.add(user_reward)

    def register_user_registration(self,airdrop_window_id,address):
        user_registration = UserRegistration(airdrop_window_id=airdrop_window_id, address=address)
        return self.add(user_registration)

    def register_claim_history(self, airdrop_id, airdrop_window_id,address, claimable_amount,unclaimable_amount,
                               transaction_status, transaction_hash):
        user_reward = ClaimHistory(
            airdrop_id=airdrop_id, airdrop_window_id=airdrop_window_id, address=address,
            claimable_amount=claimable_amount,unclaimed_amount=unclaimable_amount,
        transaction_status=transaction_status,transaction_hash=transaction_hash)
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
        total_eligibility_amount = self.fetch_total_eligibility_amount(airdrop_id,user_wallet_address)
        total_rewards = self.fetch_total_rewards_amount(
            airdrop_id, user_wallet_address)

        return total_rewards, user_wallet_address, contract_address, token_address, staking_contract_address, total_eligibility_amount

    def fetch_total_rewards_amount(self, airdrop_id, address):
        try:
            #return zero if there are no rewards, please note that MYSQL smartly sums up varchar columns and returns
            #it as a bigint if you have a very big number stored as a varchar in the rewards table.
            query = text("select ifnull( sum(ur.rewards_awarded),0) AS 'total_rewards' FROM user_rewards ur, airdrop_window aw where ur.airdrop_window_id = aw.row_id and ur.address = :address and aw.airdrop_id = :airdrop_id and aw.claim_start_period <= current_timestamp  and exists ( select 1 from airdrop_window where current_timestamp <= claim_end_period  and airdrop_id = :airdrop_id and claim_start_period <= current_timestamp ) and ur.airdrop_window_id > ( select ifnull (max(airdrop_window_id), -1) from claim_history ch where ch.address = :address and ch.transaction_status in ('SUCCESS', 'PENDING') and ch.airdrop_id = :airdrop_id) and ur.airdrop_window_id in ( SELECT airdrop_window_id FROM user_registrations  WHERE address = :address and airdrop_window_id in ( select row_id from airdrop_window where airdrop_id = :airdrop_id));")
            result = self.session.execute(
                query, {'address': address, 'airdrop_id': airdrop_id})
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
        value_retrieved = result.fetchall()[0]
        #determine the final result here, this was the service layer does not have to deal
        # with extracting 'total_rewards' from the o/p sent
        total_rewards = value_retrieved['total_rewards']
        return int(total_rewards)
    def fetch_total_eligibility_amount(self, airdrop_id, address):
        try:
            #return zero if there are no rewards, please note that MYSQL smartly sums up varchar columns and returns
            #it as a bigint if you have a very big number stored as a varchar in the rewards table.
            query = text("select ifnull( sum(ur.rewards_awarded),0) AS 'total_eligibility_rewards' FROM user_rewards ur, airdrop_window aw where ur.airdrop_window_id = aw.row_id and ur.address = :address and aw.airdrop_id = :airdrop_id and aw.claim_start_period <= current_timestamp and exists ( select 1 from airdrop_window where current_timestamp <= claim_end_period and airdrop_id = :airdrop_id and claim_start_period <= current_timestamp )  and ur.airdrop_window_id in ( SELECT airdrop_window_id FROM user_registrations WHERE address = :address and airdrop_window_id in ( select row_id from airdrop_window where airdrop_id = :airdrop_id));")
            result = self.session.execute(
                query, {'address': address, 'airdrop_id': airdrop_id})
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
        value_retrieved = result.fetchall()[0]
        total_eligible_rewards = value_retrieved['total_eligibility_rewards']
        return int(total_eligible_rewards)
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
