from utils.LambdaResponse import response
from jsonschema import validate, ValidationError
from http import HTTPStatus
from app.user.services.UserService import UserService

user_service = UserService()


class UserController:
    def registration(self, payload):

        status = HTTPStatus.BAD_REQUEST.value

        try:

            schema = {
                "type": "object",
                "properties": {
                    "airdrop_window_id": {"type": "string"},
                    "airdrop_id": {"type": "string"},
                    "address": {"type": "string"},
                    "signature": {"type": "string"},
                },
                "required": ["signature", "address", "airdrop_id", "airdrop_window_id"],
            }

            validate(instance=payload, schema=schema)
            user_service.airdrop_window_registration(payload)

            message = HTTPStatus.OK.phrase
            status = HTTPStatus.OK.value
        except ValidationError as e:
            message = e.message
        except BaseException as e:
            message = str(e)

        return response(status, message)
