import json
from unittest import TestCase
from unittest.mock import patch

from py_eth_sig_utils.signing import sign_typed_data, v_r_s_to_signature
from web3 import Web3

from airdrop.application.handlers.airdrop_handlers import user_registration
from airdrop.constants import USER_REGISTRATION_SIGNATURE_FORMAT
from airdrop.infrastructure.models import AirdropWindow, UserRegistration
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_repository import UserRepository
from airdrop.testcases.functional_testcases.test_data import AirdropData, AirdropWindowData

airdrop_repository = AirdropRepository()
airdrop_window_repository = AirdropWindowRepository()
user_repository = UserRepository()


class TestAirdropServices(TestCase):
    def setUp(self):
        self.tearDown()
        self.airdrop = airdrop_repository.register_airdrop(
            token_address=AirdropData.token_address,
            org_name=AirdropData.org_name,
            token_name=AirdropData.token_name,
            token_type=AirdropData.token_type,
            contract_address=AirdropData.contract_address,
            portal_link=AirdropData.portal_link,
            documentation_link=AirdropData.documentation_link,
            description=AirdropData.description,
            github_link_for_contract=AirdropData.github_link
        )
        self.airdrop_window = airdrop_repository.register_airdrop_window(
            airdrop_id=self.airdrop.id,
            airdrop_window_name=AirdropWindowData.airdrop_window_name,
            description=AirdropWindowData.description,
            registration_required=True,
            registration_start_period=AirdropWindowData.registration_start_date,
            registration_end_period=AirdropWindowData.registration_end_date,
            snapshot_required=True,
            claim_start_period=AirdropWindowData.claim_start_date,
            claim_end_period=AirdropWindowData.claim_end_date,
            total_airdrop_tokens=1000000
        )

    @patch("common.boto_utils.BotoUtils.get_parameter_value_from_secrets_manager")
    def test_user_registration(self, mock_get_parameter_value_from_secrets_manager):
        mock_get_parameter_value_from_secrets_manager.return_value = "1c4162244e5ec8f53a51ab6bb0a29c50432d82afd0a168e6e5c5c55c43b0a9c9"
        address = Web3.toChecksumAddress("0x4e1388Acfd6237aeED2b01Da0d4ccFe242e8F6cA")
        cardano_address = "addr_test1qqera830frgpvw9f0jj2873lwe8nd8vcsf0q0ftuqqgd9g8ucaczw427uq8y7axn2v3w8dua87kjgdgu" \
                          "rmgl38vd2hysk4dfj9"
        test_private_key = bytes.fromhex("1c4162244e5ec8f53a51ab6bb0a29c50432d82afd0a168e6e5c5c55c43b0a9c9")
        block_number = 12432452
        message = {
            "Airdrop": {
                "airdropId": self.airdrop.id,
                "airdropWindowId": self.airdrop_window.id,
                "blockNumber": block_number,
                "walletAddress": address,
                "cardanoAddress": cardano_address
            }
        }
        formatted_message = USER_REGISTRATION_SIGNATURE_FORMAT
        formatted_message["message"] = message
        signature = v_r_s_to_signature(*sign_typed_data(formatted_message, test_private_key)).hex()
        event = {
            "body": json.dumps({
                "address": address,
                "cardano_address": cardano_address,
                "airdrop_id": self.airdrop.id,
                "airdrop_window_id": self.airdrop_window.id,
                "signature": signature,
                "block_number": block_number
            })
        }
        response = user_registration(event=event, context=None)
        print(response)
        assert(response["statusCode"] == 200)
        pass

    def tearDown(self):
        user_repository.session.query(UserRegistration).delete()
        airdrop_repository.session.query(AirdropWindow).delete()
        airdrop_repository.session.query(AirdropWindow).delete()
        user_repository.session.commit()
        airdrop_repository.session.commit()
