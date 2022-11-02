from datetime import datetime as dt

from airdrop.infrastructure.models import Airdrop, AirdropWindow, UserRegistration, UserReward, ClaimHistory
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.claim_history_repo import ClaimHistoryRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.infrastructure.repositories.user_reward_repository import UserRewardRepository

airdrop_repository = AirdropRepository()
airdrop_window_repository = AirdropWindowRepository()
user_repository = UserRegistrationRepository()
user_reward_repository = UserRewardRepository()
claim_history_repo = ClaimHistoryRepository()


def load_airdrop_data(airdrop_data):
    airdrop_repository.add(
        Airdrop(
            token_address=airdrop_data.token_address,
            org_name=airdrop_data.org_name,
            token_name=airdrop_data.token_name,
            token_type=airdrop_data.token_type,
            contract_address=airdrop_data.contract_address,
            portal_link=airdrop_data.portal_link,
            documentation_link=airdrop_data.documentation_link,
            description=airdrop_data.description,
            github_link_for_contract=airdrop_data.github_link,
            airdrop_processor=airdrop_data.airdrop_processor
        )
    )
    airdrop = airdrop_repository.session.query(Airdrop) \
        .filter_by(contract_address=airdrop_data.contract_address).first()
    return airdrop


def load_airdrop_window_data(airdrop_id, airdrop_window_data):
    airdrop_window_repository.add(
        AirdropWindow(
            airdrop_id=airdrop_id,
            airdrop_window_name=airdrop_window_data.airdrop_window_name,
            description=airdrop_window_data.description,
            registration_required=airdrop_window_data.registration_required,
            registration_start_period=airdrop_window_data.registration_start_date,
            registration_end_period=airdrop_window_data.registration_end_date,
            snapshot_required=airdrop_window_data.snapshot_required,
            claim_start_period=airdrop_window_data.claim_start_date,
            claim_end_period=airdrop_window_data.claim_end_date,
            total_airdrop_tokens=airdrop_window_data.total_airdrop_tokens
        ))
    airdrop_window = airdrop_window_repository.session.query(AirdropWindow) \
        .filter(AirdropWindow.airdrop_id == airdrop_id) \
        .filter(AirdropWindow.airdrop_window_name == airdrop_window_data.airdrop_window_name) \
        .first()
    return airdrop_window


def load_user_reward_data(airdrop_id, airdrop_window_id, airdrop_user):
    user_reward_repository.add(
        UserReward(
            airdrop_id=airdrop_id,
            airdrop_window_id=airdrop_window_id,
            address=airdrop_user.address,
            condition="",
            rewards_awarded=1,
            score=1,
            normalized_score=1
        )
    )


def load_airdrop_user_registration(airdrop_window_id, airdrop_user, airdrop_name=None):
    address=""
    if airdrop_name == "Loyalty Airdrop":
        address = airdrop_user.cardano_address
        cardano_wallet_name = airdrop_user.cardano_wallet_name
    signature_details = {"message": {"Airdrop": {"address": address,"cardano_wallet_name":cardano_wallet_name,"block_no": 54321}}}
    user_repository.add(
        UserRegistration(
            address=airdrop_user.address,
            airdrop_window_id=airdrop_window_id,
            registered_at=dt.utcnow(),
            receipt_generated=airdrop_user.receipt_generated,
            user_signature="",
            signature_details=signature_details,
            user_signature_block_number=airdrop_user.signature_details["block_no"]
        )
    )


def clear_database():
    claim_history_repo.session.query(ClaimHistory).delete()
    user_reward_repository.session.query(UserReward).delete()
    user_repository.session.query(UserRegistration).delete()
    airdrop_repository.session.query(Airdrop).delete()
    airdrop_repository.session.query(AirdropWindow).delete()
    user_repository.session.commit()
    airdrop_repository.session.commit()
    claim_history_repo.session.commit()
