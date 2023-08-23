"""REST API models for the orchestrator commands package"""

from marshmallow import Schema
from marshmallow.fields import String, Integer, Nested, List


class CommandSchema(Schema):
    """REST ressource orchestrator single command"""

    id = Integer(required=True, allow_none=False)
    name = String(required=True, allow_none=False)


class CommandsListSchema(Schema):
    """REST ressource orchestrator commands list"""

    commands = List(Nested(CommandSchema), required=True)

class CommandsQuerySchema(Schema):
    """REST ressource orchestrator query commands list"""

    commands_ids = String(required=True, allow_none=False)
