from enum import Enum
import json

from web3 import Web3

from airdrop.infrastructure.models import UserRegistration
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.utils import Utils
from common.logger import get_logger

logger = get_logger(__name__)


class RejuveProcesses(Enum):
    CONVERT_FROM_STR_TO_JSON = "convert_str_to_json"
    CHANGE_ADDRESS_FORMAT = "change_address_format"


class ConverterFromStrToJSON:
    def __init__(self, airdrop_id, window_id, address=None):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self.address = address

    def receive_all_registrations(self) -> list[UserRegistration]:
        logger.info("Processing the receiving all registrations for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")
        if self.address:
            _, registration = UserRegistrationRepository().get_user_registration_details(address=self.address,
                                                                                         airdrop_window_id=self._window_id)
            registrations = [registration]
        else:
            _, registrations = UserRegistrationRepository().get_user_registration_details(airdrop_window_id=self._window_id)
        return registrations

    def change_signature_details(self, registrations: list[UserRegistration]) -> None:
        logger.info("Processing the changing signature details for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")

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

    def process_convert(self) -> str:
        logger.info("Processing the converting for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")

        registrations = self.receive_all_registrations()
        if not registrations:
            raise Exception("0 registrations received from db")
        self.change_signature_details(registrations)

        return (f"{len(registrations)} registrations changed on "
                f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")


class ChangerAddressFormat:
    def __init__(self, airdrop_id, window_id, address=None):
        self._airdrop_id = airdrop_id
        self._window_id = window_id
        self.address = address

    def receive_all_registrations(self) -> list[UserRegistration]:
        logger.info("Processing the receiving all registrations for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")
        if self.address:
            _, registration = UserRegistrationRepository().get_user_registration_details(address=self.address,
                                                                                         airdrop_window_id=self._window_id)
            registrations = [registration]
        else:
            _, registrations = UserRegistrationRepository().get_user_registration_details(airdrop_window_id=self._window_id)
        return registrations

    def change_address_format(self, registrations: list[UserRegistration]) -> None:
        logger.info("Processing the changing address format for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")

        for addr in registrations:
            if (isinstance(addr.address, str) and
                Utils().recognize_blockchain_network(addr.address) == "Ethereum"):
                user_address = Web3.to_checksum_address(addr.address)
                logger.info(f"Old format {addr.address = }. New format {user_address = }")
                UserRegistrationRepository().update_registration_address(
                    airdrop_window_id=self._window_id,
                    old_address=addr.address,
                    new_address=user_address
                )
                logger.info("Successfully updated")
            else:
                logger.info(f"Address = {addr.address} is not available for updating")

    def process_change(self) -> str:
        logger.info("Processing the address format changing for the "
                    f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")

        registrations = self.receive_all_registrations()
        if not registrations:
            raise Exception("0 registrations received from db")
        self.change_address_format(registrations)

        return (f"{len(registrations)} registrations changed on "
                f"airdrop_id = {self._airdrop_id}, window_id = {self._window_id}")
