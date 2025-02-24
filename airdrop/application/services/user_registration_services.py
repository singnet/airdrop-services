from http import HTTPStatus

from jsonschema import validate, ValidationError

from airdrop.application.services.airdrop_services import AirdropServices
from airdrop.constants import AirdropClaimStatus
from airdrop.constants import ELIGIBILITY_SCHEMA, USER_REGISTRATION_SCHEMA
from airdrop.infrastructure.models import AirdropWindow
from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from airdrop.infrastructure.repositories.airdrop_window_repository import AirdropWindowRepository
from airdrop.infrastructure.repositories.user_registration_repo import UserRegistrationRepository
from airdrop.utils import Utils, datetime_in_utcnow
from common.logger import get_logger

logger = get_logger(__name__)
utils = Utils()


class UserRegistrationServices:

    @staticmethod
    def eligibility(inputs):
        status = HTTPStatus.BAD_REQUEST
        try:
            validate(instance=inputs, schema=ELIGIBILITY_SCHEMA)
            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if airdrop is None:
                raise Exception("Airdrop id is not valid.")

            airdrop_window = AirdropWindowRepository().get_airdrop_window_by_id(airdrop_window_id,
                                                                                airdrop_id=airdrop_id)
            if airdrop_window is None:
                raise Exception("Airdrop window id is not valid.")

            airdrop_class = AirdropServices.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            is_user_eligible = airdrop_object.check_user_eligibility(address)

            rewards_awarded = AirdropRepository().fetch_total_rewards_amount(airdrop_id, address)

            user_registered, user_registration = UserRegistrationRepository(). \
                get_user_registration_details(address, airdrop_window_id)

            is_airdrop_window_claimed = False
            is_claimable = False
            airdrop_claim_status = AirdropWindowRepository().is_airdrop_window_claimed(airdrop_window_id, address)

            if airdrop_claim_status == AirdropClaimStatus.SUCCESS.value:
                is_airdrop_window_claimed = True
            else:
                if rewards_awarded > 0:
                    is_claimable = True
            # if the user has not claimed yet and there are rewards pending to be claimed , then let the user claim
            # rewards awarded will have some value ONLY when the claim window opens and the user has unclaimed rewards
            # a claim in progress ~ PENDING will also be considered as claimed ( we don't want the user to end up losing
            # gas in trying to claim again)
            registration_id, reject_reason, registration_details = "", None, dict()
            if user_registered:
                registration_id = user_registration.receipt_generated
                reject_reason = user_registration.reject_reason
                registration_details = {
                    "registration_id": user_registration.receipt_generated,
                    "reject_reason": user_registration.reject_reason,
                    "other_details": user_registration.signature_details.get("message", {}).get("Airdrop", {}),
                    "registered_at": str(user_registration.registered_at),
                }
            response = {
                "is_eligible": is_user_eligible,
                "is_already_registered": user_registered,
                "is_airdrop_window_claimed": is_airdrop_window_claimed,
                "airdrop_window_claim_status": airdrop_claim_status,
                "user_address": address,
                "airdrop_id": airdrop_id,
                "airdrop_window_id": airdrop_window_id,
                "reject_reason": reject_reason,
                "airdrop_window_rewards": rewards_awarded,
                "registration_id": registration_id,
                "is_claimable": is_claimable,
                "registration_details": registration_details
            }
            status = HTTPStatus.OK

        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response

    def register(self, inputs: dict):
        try:
            validate(instance=inputs, schema=USER_REGISTRATION_SCHEMA)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if not airdrop:
                raise Exception("Airdrop id is not valid.")

            airdrop_window_repo = AirdropWindowRepository()
            airdrop_window = airdrop_window_repo.get_airdrop_window_by_id(airdrop_window_id)
            if airdrop_window is None:
                raise Exception("Airdrop window id is not valid.")

            airdrop_class = AirdropServices.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            response: list | str = airdrop_object.register(inputs)
        except ValidationError as e:
            return HTTPStatus.BAD_REQUEST, repr(e)
        except BaseException as e:
            return HTTPStatus.BAD_REQUEST, repr(e)
        return HTTPStatus.OK, response

    def update_registration(self, inputs):
        try:
            validate(instance=inputs, schema=USER_REGISTRATION_SCHEMA)

            airdrop_id = inputs["airdrop_id"]
            airdrop_window_id = inputs["airdrop_window_id"]
            address = inputs["address"].lower()
            signature = inputs["signature"]
            block_number = inputs["block_number"]

            airdrop = AirdropRepository().get_airdrop_details(airdrop_id)
            if not airdrop:
                raise Exception("Airdrop id is not valid.")

            airdrop_window_repo = AirdropWindowRepository()
            airdrop_window = airdrop_window_repo.get_airdrop_window_by_id(airdrop_window_id)
            if airdrop_window is None:
                raise Exception("Airdrop window id is not valid.")

            airdrop_class = AirdropServices.load_airdrop_class(airdrop)
            airdrop_object = airdrop_class(airdrop_id, airdrop_window_id)

            formatted_message = airdrop_object.match_signature(inputs)

            if not airdrop_object.allow_update_registration:
                raise Exception("Registration update not allowed.")

            airdrop_windows: list[AirdropWindow] = airdrop_window_repo.get_airdrop_windows(airdrop_id) \
                if airdrop_object.register_all_window_at_once \
                else [airdrop_window]

            response = []
            registration_repo = UserRegistrationRepository()
            utc_now = datetime_in_utcnow()
            for window in airdrop_windows:
                try:
                    is_registered, receipt = registration_repo.is_registered_user(window.id, address)
                    is_claimed = airdrop_window_repo.is_airdrop_window_claimed(window.id, address)
                    assert is_registered, "not registered"
                    assert not is_claimed, "already claimed"
                    assert window.claim_end_period > utc_now, "claim period is over"
                    registration_repo.update_registration(window.id, address,
                                                          signature=signature,
                                                          signature_details=formatted_message,
                                                          block_number=block_number,
                                                          registered_at=utc_now)
                    response.append({"airdrop_window_id": window.id, "receipt": receipt})
                except AssertionError as e:
                    warning = f"Airdrop window {window.id} registration update failed ({str(e)})"
                    if len(airdrop_windows) == 1 and window == airdrop_window:
                        raise Exception(warning)
                    response.append({"airdrop_window_id": window.id, "warning": warning})

        except (ValidationError, BaseException) as e:
            return HTTPStatus.BAD_REQUEST, repr(e)
        return HTTPStatus.OK, response
