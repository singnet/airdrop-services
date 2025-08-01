from typing import Optional, Tuple, Union

from airdrop.constants import CARDANO_ADDRESS_PREFIXES, Blockchain, CardanoEra
from airdrop.infrastructure.models import UserRegistration
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.utils import Utils


class CommonLogicService:

    @staticmethod
    def get_user_registration_details(
            address: str,
            airdrop_window_id: int,
            registration_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Union[UserRegistration, list[UserRegistration]]]]:
        registration_repo = UserRegistrationRepository()
        network = Utils.recognize_blockchain_network(address)
        if (network == Blockchain.ETHEREUM.value or
            address.startswith(tuple(CARDANO_ADDRESS_PREFIXES[CardanoEra.BYRON]))):
            return registration_repo.get_user_registration_details(
                address=address,
                airdrop_window_id=airdrop_window_id,
                registration_id=registration_id
            )
        elif network == Blockchain.CARDANO.value:
            payment_part, staking_part = Utils.get_payment_staking_parts(address)
            return registration_repo.get_user_registration_details(
                payment_part=payment_part,
                staking_part=staking_part,
                airdrop_window_id=airdrop_window_id,
                registration_id=registration_id
            )
