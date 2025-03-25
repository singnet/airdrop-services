import json

from airdrop.infrastructure.models import UserRegistration
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from common.logger import get_logger

logger = get_logger(__name__)


class ConverterFromStrToJSON:
    def __init__(self, airdrop_id, window_id):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self.address = None

    def receive_all_registrations(self) -> list[UserRegistration]:
        logger.info("Processing the receiving all registrations for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")
        if self.address:
            _, registrations = UserRegistrationRepository().get_user_registration_details(address=self.address,
                                                                                          airdrop_window_id=self._window_id)
        else:
            _, registrations = UserRegistrationRepository().get_user_registration_details(airdrop_window_id=self._window_id)
        return registrations

    def change_signature_details(self, registrations: list[UserRegistration]):
        logger.info("Processing the changing signature details for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")
        if isinstance(registrations, UserRegistration):
            signature_details = json.loads(registrations.signature_details)
            logger.info(f"{registrations.address = } {signature_details = }")
            UserRegistrationRepository().update_registration(
                airdrop_window_id=self._window_id,
                address=registrations.address,
                signature_details=signature_details,
            )
            logger.info("Successfully updated")
            return

        for addr in registrations:
            if isinstance(addr.signature_details, str):
                signature_details = json.loads(addr.signature_details)
                logger.info(f"{addr.address = } {signature_details = }")
                UserRegistrationRepository().update_registration(
                    airdrop_window_id=self._window_id,
                    address=addr.address,
                    signature_details=signature_details,
                )
                logger.info("Successfully updated")

    def process_convert(self):
        logger.info("Processing the converting for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")

        registrations = self.receive_all_registrations()
        if not registrations:
            raise Exception("0 registrations received from db")
        self.change_signature_details(registrations)

        if isinstance(registrations, UserRegistration):
            return (f"1 registration changed on "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")
        return (f"{len(registrations)} registrations changed on "
                f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")