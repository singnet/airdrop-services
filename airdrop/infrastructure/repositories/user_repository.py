from airdrop.infrastructure.repositories.base_repository import BaseRepository
from airdrop.infrastructure.models import UserRegistration
from datetime import datetime


class UserRepository(BaseRepository):
    def is_registered_user(self, airdrop_window_id, address):
        return (
            self.session.query(UserRegistration.id)
            .filter(UserRegistration.airdrop_window_id == airdrop_window_id)
            .filter(UserRegistration.address == address)
            .filter(UserRegistration.registered_at != None)
            .first()
        )

    def register_user(self, airdrop_window_id, address):
        self.session.query(UserRegistration).filter(
            UserRegistration.address == address
        ).filter(UserRegistration.airdrop_window_id == airdrop_window_id).filter(
            UserRegistration.is_eligible == True
        ).update(
            {UserRegistration.registered_at: datetime.utcnow()},
            synchronize_session=False,
        )
        self.session.commit()
