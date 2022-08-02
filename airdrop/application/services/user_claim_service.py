from http import HTTPStatus

import requests

from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.config import TokenTransferCardanoService, SLACK_HOOK
from airdrop.constants import AirdropClaimStatus
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.claim_history_repo import ClaimHistoryRepository
from common.logger import get_logger
from common.utils import Utils

logger = get_logger(__name__)
utils = Utils()


class UserClaimService:
    def __init__(self, airdrop_id):
        self.airdrop_id = airdrop_id
        self.airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
        self.airdrop_class = AirdropServices().load_airdrop_class(self.airdrop)

    def prepare_token_transfer_cardano_service_payload(self, claims):
        token = self.airdrop.token_name
        from_address_wallet_name = self.airdrop_class(self.airdrop_id).claim_address
        to_addresses = []
        for claim in claims:
            to_addresses.append({"address": claim["cardano_address"], "amount": claim.claimable_amount})
        payload = {
            "token": token,
            "from_address_wallet_name": from_address_wallet_name,
            "to_addresses": to_addresses,
        }
        return payload

    @staticmethod
    def invoke_token_transfer_cardano_service(payload):
        response = requests.post(TokenTransferCardanoService.url, json=payload,
                                 headers=TokenTransferCardanoService.headers)
        if response.status_code != HTTPStatus.OK.value:
            logger.info("Error calling token transfer cardano service.")
            return {}
        return response

    def initiate_claim_for_users(self):
        # Fetch eligible claim records
        blockchain_method = "token_transfer"
        transaction_status = AirdropClaimStatus.CLAIM_INITIATED.value
        claims = ClaimHistoryRepository().get_pending_claims_for_given_airdrop_id(self.airdrop_id, blockchain_method)

        if not claims:
            logger.info(f"No pending claims for airdrop id {self.airdrop_id}")

        # Update transaction as claim initiated
        for claim in claims:
            ClaimHistoryRepository().update_claim_status(claim["address"], claim["airdrop_window_id"],
                                                         blockchain_method, transaction_status)

        # Invoke token transfer cardano service
        token_transfer_service_payload = self.prepare_token_transfer_cardano_service_payload(claims)
        response = self.invoke_token_transfer_cardano_service(token_transfer_service_payload)
        transaction_id = response.get("data", {}).get("transaction_id", "")
        if transaction_status and len(transaction_status) > 0:
            transaction_status = AirdropClaimStatus.CLAIM_SUBMITTED.value
        else:
            transaction_status = AirdropClaimStatus.CLAIM_FAILED.value
            utils.report_slack(type=0, slack_message="Token Transfer Cardano Service Failed!", slack_config=SLACK_HOOK)
            transaction_id = None

        # Update claim status as CLAIM_FAILED/CLAIM_SUBMITTED
        for claim in claims:
            ClaimHistoryRepository().update_claim_status(claim["address"], claim["airdrop_window_id"],
                                                         blockchain_method, transaction_status, transaction_id)
        return {"status": "success"}
