from airdrop.infrastructure.repositories.airdrop_repository import AirdropRepository
from jsonschema import validate, ValidationError
from http import HTTPStatus


class AirdropServices:
    def get_airdrops_schedule(self, inputs):
        status = HTTPStatus.BAD_REQUEST

        try:
            schema = {
                "type": "object",
                "properties": {"limit": {"type": "string"}, "skip": {"type": "string"}},
                "required": ["limit", "skip"],
            }

            validate(instance=inputs, schema=schema)

            skip = inputs["skip"]
            limit = inputs["limit"]

            schedule = AirdropRepository().get_airdrops_schedule(limit, skip)
            response = {"schedule": schedule}
            status = HTTPStatus.OK
        except ValidationError as e:
            response = e.message
        except BaseException as e:
            response = str(e)

        return status, response
