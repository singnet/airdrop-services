from airdrop.domain.models.airdrop_schedule import AirdropSchedule
from airdrop.domain.models.airdrop_window import AirdropWindow
from airdrop.domain.models.airdrop_user_details import AirdropUserDetails
from airdrop.domain.models.airdrop_claim_history import AirdropClaimHistory
from airdrop.domain.models.airdrop_stake_claim import AirdropStakeClaim


class AirdropFactory:
    @staticmethod
    def convert_stake_claim_details_to_model(airdrop_id, window_id, address, claimable_tokens_to_wallet, stakable_tokens, is_stakable, token_name):
        return AirdropStakeClaim(
            airdrop_id, window_id, address, claimable_tokens_to_wallet, stakable_tokens, is_stakable, token_name
        ).to_dict()

    @staticmethod
    def convert_airdrop_schedule_model_to_entity_model(airdrop):
        return AirdropSchedule(
            airdrop.id,
            airdrop.token_name,
            airdrop.description,
            airdrop.portal_link,
            airdrop.documentation_link,
            airdrop.github_link_for_contract,
            airdrop.airdrop_rules,
            airdrop.windows
        ).to_dict()

    @staticmethod
    def convert_airdrop_window_model_to_entity_model(window):
        return AirdropWindow(
            window.airdrop_id,
            window.id,
            window.airdrop_window_name,
            window.description,
            str(window.registration_start_period),
            str(window.registration_end_period),
        ).to_dict()

    @staticmethod
    def convert_airdrop_window_user_model_to_entity_model(user):
        return AirdropUserDetails(
            user.airdrop_window.airdrop_id,
            user.airdrop_window.id,
            user.airdrop_window.airdrop_window_name,
            user.address,
            str(user.registered_at)
        ).to_dict()

    @staticmethod
    def convert_claim_history_model_to_entity_model(claim):
        return AirdropClaimHistory(
            claim.airdrop_id,
            claim.airdrop_window_id,
            claim.address,
            claim.transaction_status,
            claim.transaction_hash,
            claim.claimable_amount,
            str(claim.claimed_on),
            claim.user_registrations,
            claim.blockchain_method
        ).to_dict()
