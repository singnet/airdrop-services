from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from airdrop.constants import AirdropClaimStatus
from airdrop.domain.factory.airdrop_factory import AirdropFactory
from airdrop.infrastructure.models import AirdropWindow, UserRegistration, UserReward, UserNotifications
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.base_repository import BaseRepository


class UserRegistrationRepository(BaseRepository):

    def subscribe_to_notifications(self, email, airdrop_id):
        try:

            is_existing_email = self.session.query(UserNotifications.id).filter(
                UserNotifications.email == email).filter(UserNotifications.airdrop_id == airdrop_id).first()

            if is_existing_email is None:
                user_notifications = UserNotifications(email=email, airdrop_id=airdrop_id)
                self.add(user_notifications)
            else:
                raise Exception('Email already subscribed to notifications')

        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def check_rewards_awarded(self, airdrop_id, airdrop_window_id, address):
        try:
            is_eligible = (
                self.session.query(UserReward)
                .filter(UserReward.address == address)
                .filter(UserReward.airdrop_id == airdrop_id)
                .filter(UserReward.airdrop_window_id == airdrop_window_id)
                .first()
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

        total_rewards = AirdropRepository().fetch_total_rewards_amount(airdrop_id, address)
        eligible_for_window = False
        # Simplified the logic, if rewards_awarded > 0 => the user is eligible
        if is_eligible is not None and int(is_eligible.rewards_awarded) > 0:
            eligible_for_window = True
        else:
            eligible_for_window = False
        return eligible_for_window, total_rewards

    def airdrop_window_user_details(self, airdrop_window_id, address):
        user_data = (
            self.session.query(UserRegistration)
            .join(
                AirdropWindow,
                AirdropWindow.id == UserRegistration.airdrop_window_id,
            )
            .filter(UserRegistration.airdrop_window_id == airdrop_window_id)
            .filter(UserRegistration.address == address)
            .filter(UserRegistration.registered_at != None)
            .first()
        )

        user_details = None

        if user_data is not None:
            user_details = AirdropFactory.convert_airdrop_window_user_model_to_entity_model(
                user_data)

        return user_details

    def get_reject_reason(self, airdrop_window_id, address):
        registration = (
            self.session.query(UserRegistration.reject_reason)
            .filter(UserRegistration.airdrop_window_id == airdrop_window_id)
            .filter(UserRegistration.address == address)
            .first()
        )

        return registration.reject_reason if registration is not None else None

    def is_registered_user(self, airdrop_window_id, address):
        is_registered_user = (
            self.session.query(UserRegistration)
            .filter(UserRegistration.airdrop_window_id == airdrop_window_id)
            .filter(UserRegistration.address == address)
            .filter(UserRegistration.registered_at != None)
            .first()
        )

        if is_registered_user is None:
            return False, ""
        else:
            return True, is_registered_user.receipt_generated

    def register_user(self, airdrop_window_id, address, receipt, signature, signature_details, block_number):
        user = UserRegistration(
            airdrop_window_id=airdrop_window_id,
            address=address,
            registered_at=datetime.utcnow(),
            receipt_generated=receipt,
            user_signature=signature,
            signature_details=signature_details,
            user_signature_block_number=block_number
        )
        self.add(user)

    def update_registration(self, airdrop_window_id, address, **kwargs):
        registered_at = kwargs.get("registered_at")
        reject_reason = kwargs.get("reject_reason")
        receipt = kwargs.get("receipt")
        signature = kwargs.get("signature")
        signature_details = kwargs.get("signature_details")
        block_number = kwargs.get("block_number")
        registration = self.session.query(UserRegistration) \
            .filter_by(airdrop_window_id=airdrop_window_id, address=address).one()
        if registered_at is not None:
            registration.registered_at = registered_at
        if reject_reason is not None:
            registration.reject_reason = reject_reason
        if receipt is not None:
            registration.receipt_generated = receipt
        if signature is not None:
            registration.user_signature = signature
        if signature_details is not None:
            registration.signature_details = signature_details
        if block_number is not None:
            registration.user_signature_block_number = block_number
        self.session.commit()
        return registration

    def is_user_eligible_for_given_window(self, address, airdrop_id, airdrop_window_id):
        user_reward = self.session.query(UserReward) \
            .filter(UserReward.address == address) \
            .filter(UserReward.airdrop_id == airdrop_id) \
            .filter(UserReward.airdrop_window_id == airdrop_window_id) \
            .first()
        if user_reward and int(user_reward.rewards_awarded) > 0:
            return True
        else:
            return False

    def get_user_registration_details(self, address=None, airdrop_window_id=None, registration_id=None):
        query = self.session.query(UserRegistration).filter(UserRegistration.registered_at != None)
        if address:
            query = query.filter(UserRegistration.address == address)
        if airdrop_window_id:
            query = query.filter(UserRegistration.airdrop_window_id == airdrop_window_id)
        if registration_id:
            query = query.filter(UserRegistration.receipt_generated == registration_id)
        user_registrations = query.all()
        registration_count = len(user_registrations)
        if registration_count:
            return True, user_registrations[0] if registration_count == 1 else user_registrations
        return False, None

    def get_unclaimed_reward(self, airdrop_id, address):
        in_progress_or_completed_tx_statuses = (
            AirdropClaimStatus.SUCCESS.value, AirdropClaimStatus.PENDING.value,
            AirdropClaimStatus.CLAIM_INITIATED.value, AirdropClaimStatus.CLAIM_SUBMITTED.value,
            AirdropClaimStatus.CLAIM_FAILED.value
        )
        try:
            query = text("SELECT IFNULL( sum(ur.rewards_awarded),0) AS 'unclaimed_reward' FROM user_rewards ur, "
                         "airdrop_window aw WHERE ur.airdrop_window_id = aw.row_id AND ur.address = :address "
                         "AND aw.airdrop_id = :airdrop_id AND aw.claim_start_period <= current_timestamp "
                         "AND EXISTS (SELECT 1 FROM airdrop_window WHERE current_timestamp <= claim_end_period "
                         "AND airdrop_id = :airdrop_id AND claim_start_period <= current_timestamp) "
                         "AND ur.airdrop_window_id > (SELECT ifnull (max(airdrop_window_id), -1) from claim_history ch "
                         "where ch.airdrop_id = :airdrop_id and ch.address = :address "
                         "and ch.transaction_status in :in_progress_or_completed_tx_statuses)")
            result = self.session.execute(query, {
                "address": address,
                "airdrop_id": airdrop_id,
                "in_progress_or_completed_tx_statuses": in_progress_or_completed_tx_statuses
            })
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e
        unclaimed_reward = int(result.fetchall()[0]["unclaimed_reward"])
        return unclaimed_reward
