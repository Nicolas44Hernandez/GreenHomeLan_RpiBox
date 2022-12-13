"""REST API models for system version package"""

from marshmallow import Schema
from marshmallow.fields import Str


class SystemVersionSchema(Schema):
    """REST ressource for system version"""

    version = Str(required=True, allow_none=False)
