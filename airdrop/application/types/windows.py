from dataclasses import dataclass
from typing import Optional
from airdrop.constants import AirdropClaimStatus, UserClaimStatus


@dataclass
class RegistrationDetails:
    registration_id: str
    registered_at: str
    other_details: dict
    reject_reason: Optional[str] = ""


@dataclass
class WindowRegistrationData:
    window_id: int
    airdrop_window_claim_status: Optional[AirdropClaimStatus]
    claim_status: UserClaimStatus
    registration_details: Optional[RegistrationDetails]