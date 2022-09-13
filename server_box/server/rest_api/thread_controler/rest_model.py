"""REST API models for Thread package"""

from marshmallow import Schema
from marshmallow.fields import Str


class NodeSchema(Schema):
    """REST ressource for Thread node"""

    name = Str(required=True, allow_none=False)
    mac = Str(required=True, allow_none=False)
    server_url = Str(required=True, allow_none=False)
