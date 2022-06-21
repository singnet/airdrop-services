import json
import web3
from web3 import Web3
from unittest import TestCase
from eth_account.messages import encode_defunct
from airdrop.config import NETWORK
from airdrop.application.handlers.airdrop_handlers import user_registration
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_repository import UserRepository
from airdrop.testcases.functional_testcases.test_data import AirdropData, AirdropWindowData
from airdrop.infrastructure.models import Airdrop, AirdropWindow, UserRegistration

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

    # def test_user_registration(self):
    #     address = Web3.toChecksumAddress("0x4e1388Acfd6237aeED2b01Da0d4ccFe242e8F6cA")
    #     cardano_address = "addr_test1qqera830frgpvw9f0jj2873lwe8nd8vcsf0q0ftuqqgd9g8ucaczw427uq8y7axn2v3w8dua87kjgdgu" \
    #                       "rmgl38vd2hysk4dfj9 "
    #     test_private_key = "1c4162244e5ec8f53a51ab6bb0a29c50432d82afd0a168e6e5c5c55c43b0a9c9"
    #     block_number = 12432452
    #     data_types = ["uint256", "uint256", "uint256", "address", "string"]
    #     # new_data_type = { "Airdrop": {
    #     #     airdropId: airdropId.toString(),
    #     #     airdropWindowId: airdropWindowId.toString(),
    #     #     blockNumber: blockNumber.toString(),
    #     #     walletAddress: account,
    #     # },
    #     web3.eth.recover_sign
    #     values = [self.airdrop.id, self.airdrop_window.id, block_number, address, cardano_address]
    #     message = web3.Web3.soliditySha3(data_types, values, )
    #     message_hash = encode_defunct(message)
    #     web3_object = Web3(web3.providers.HTTPProvider(NETWORK['http_provider']))
    #     signed_message = web3.eth.signTypedData()
    #     signed_message = web3_object.eth.account.sign_message(message_hash, private_key=test_private_key)
    #     signature = signed_message.signature.hex()
    #     event = {
    #         "body": json.dumps({
    #             "address": address,
    #             "cardano_address": cardano_address,
    #             "airdrop_id": self.airdrop.id,
    #             "airdrop_window_id": self.airdrop_window.id,
    #             "signature": signature,
    #             "block_number": block_number
    #         })
    #     }
    #     response = user_registration(event=event, context=None)
    #     print(response)
    #     pass

    # def test_user_registration1(self):
    #     address = "0x4e1388Acfd6237aeED2b01Da0d4ccFe242e8F6cA"
    #     # signature = "0xa0d01d8b7f5bfb8eefc409bf6a5ce5416bdc88939768a42d6851a724ea8cc1ea27a9af68188b81fd56c65341b7a1ba" \
    #     #             "fa78217e93c5f6aad487e5b9f83fcd90151b"
    #     signature = "0xdb8b2c1326c9ea95f3e28b228186e232c87f0ed9cbd1c84c2231c5f7be3018ab38e6a85fb4726a1d5dd1f0d79766ac" \
    #                 "8e6d4608a0fe87d593b24ed70a4ff52c401c"
    #     event = {
    #         "body": json.dumps({
    #             "address": address,
    #             "cardano_address": cardano_address,
    #             "airdrop_id": 1,
    #             "airdrop_window_id": 9,
    #             "signature": signature,
    #             "block_number": 12432452
    #         })
    #     }
    #     response = user_registration(event=event, context=None)
    #     print(response)
    #     pass

    def test_typed_signature(self):
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "AirdropSignatureTypes": [
                    {"name": "airdropId", "type": "uint256"},
                    {"name": "airdropWindowId", "type": "uint256"},
                    {"name": "blockNumber", "type": "uint256"},
                    {"name": "walletAddress", "type": "address"},
                    {"name": "cardanoAddress", "type": "string"},
                ],
                "Mail": [
                    {"name": "Airdrop", "type": "AirdropSignatureTypes"},
                ],
            },
            "primaryType": "Mail",
            "domain": {
                "name": "Nunet Airdrop",
                "version": "1",
                "chainId": 3,
            },
            "message": {
                "Airdrop": {
                    "airdropId": 1,
                    "airdropWindowId": 9,
                    "blockNumber": 12432452,
                    "walletAddress": "0x4e1388Acfd6237aeED2b01Da0d4ccFe242e8F6cA",
                    "cardanoAddress": "addr_test1qqera830frgpvw9f0jj2873lwe8nd8vcsf0q0ftuqqgd9g8ucaczw427uq8y7axn2v3w8dua87kjgdgurmgl38vd2hysk4dfj9",
                },

            },
        }
        from py_eth_sig_utils import utils
        private_key = bytes.fromhex("1c4162244e5ec8f53a51ab6bb0a29c50432d82afd0a168e6e5c5c55c43b0a9c9")
        from py_eth_sig_utils.signing import sign_typed_data, v_r_s_to_signature, recover_typed_data, signature_to_v_r_s
        signature = v_r_s_to_signature(*sign_typed_data(typed_data, private_key)).hex()
        print(f"signature == {signature}")
        signer_address = recover_typed_data(typed_data, *signature_to_v_r_s(bytes.fromhex(signature)))
        print(signer_address)

    def tearDown(self):
        user_repository.session.query(UserRegistration).delete()
        airdrop_repository.session.query(AirdropWindow).delete()
        airdrop_repository.session.query(AirdropWindow).delete()
        user_repository.session.commit()
        airdrop_repository.session.commit()
