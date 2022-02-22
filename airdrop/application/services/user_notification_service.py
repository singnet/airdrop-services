from jsonschema import validate, ValidationError, FormatChecker
from http import HTTPStatus
from airdrop.infrastructure.repositories.user_repository import UserRepository


class UserNotificationService:
    def subscribe_to_notifications(self, inputs):
        status = HTTPStatus.BAD_REQUEST
        try:
            schema = {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                },
                "required": ["email"],
            }

            validate(instance=inputs, schema=schema,
                     format_checker=FormatChecker())
            email = inputs["email"]
            airdrop_id = inputs["airdrop_id"]
            UserRepository().subscribe_to_notifications(email,airdrop_id)
            response = HTTPStatus.OK.phrase
            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response
