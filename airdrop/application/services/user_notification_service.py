
from jsonschema import validate, ValidationError


class UserNotificationService:
    def subscribe_to_notifications(self, inputs):
        try:
            schema = {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "airdrop_id": {"type": "string"},
                },
                "required": ["address", "airdrop_id"],
            }

            validate(instance=inputs, schema=schema)
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response
