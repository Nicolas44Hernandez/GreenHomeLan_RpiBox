"""REST API models for Thread package"""

from marshmallow import Schema
from marshmallow.fields import Str, Bool


class NodeSchema(Schema):
    """REST ressource for Thread node"""

    id = Str(required=True, allow_none=False)
    last_seen = Str(required=True, allow_none=False)


class ThreadNetworkSetupSchema(Schema):
    """REST ressource for Thread network setup"""

    ipv6_otbr = Str(required=True, allow_none=False)
    ipv6_mesh = Str(required=True, allow_none=False)
    dataset_key = Str(required=True, allow_none=False)
