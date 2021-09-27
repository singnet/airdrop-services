from database.repositories.AirdropWIndowRepository import AirdropWIndowRepository
from database.repositories.UserRegistrationRepository import UserRegistrationRepository
from utils.Web3 import verify_signature
from datetime import datetime


class UserService:
    def airdrop_window_registration(self, inputs):

        airdrop_id = inputs["airdrop_id"]
        airdrop_window_id = inputs["airdrop_window_id"]
        address = inputs["address"].lower()
        signature = inputs["signature"]

        verify_signature(airdrop_id, airdrop_window_id, address, signature)

        is_open_airdrop_window = self.get_user_airdrop_window(
            airdrop_id, airdrop_window_id
        )

        if is_open_airdrop_window is None:
            raise Exception(
                "Airdrop window is not accepting registration at this moment"
            )

        is_eligible_user = UserRegistrationRepository().is_eligible_user(
            airdrop_window_id, address
        )

        if is_eligible_user is None:
            raise Exception("Address is not eligible for this airdrop window")

        is_registered_user = self.is_elgible_registered_user(airdrop_window_id, address)

        if is_registered_user is not None:
            raise Exception("Address is already registered for this airdrop window")

        UserRegistrationRepository().register_user(airdrop_window_id, address)

    def get_user_airdrop_window(self, airdrop_id, airdrop_window_id):
        now = datetime.utcnow()
        return AirdropWIndowRepository().is_open_airdrop_window(
            airdrop_id, airdrop_window_id, now
        )

    def is_elgible_registered_user(self, airdrop_window_id, address):
        return UserRegistrationRepository().is_registered_user(
            airdrop_window_id, address
        )
