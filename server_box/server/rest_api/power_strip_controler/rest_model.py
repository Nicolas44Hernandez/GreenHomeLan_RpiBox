"""REST API models for relays manager package"""

from marshmallow import Schema
from marshmallow.fields import Boolean, List, Integer, Nested, DateTime

# Datetime naive format to use for serialization
API_NAIVE_DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"


class SingleRelayStatusSchema(Schema):
    """REST ressource for single relay status"""

    relay_number = Integer(required=True, allow_none=False)
    status = Boolean(required=True, allow_none=False)


class RelaysStatusResponseSchema(Schema):
    """REST ressource for relays status response"""

    relay_statuses = List(Nested(SingleRelayStatusSchema), required=True)
    timestamp = DateTime(required=True, format=API_NAIVE_DATETIME_FORMAT)


class RelaysStatusQuerySchema(Schema):
    """REST ressource for relays status query"""

    relay_1 = Boolean(required=False, allow_none=True, default=None)
    relay_2 = Boolean(required=False, allow_none=True, default=None)
    relay_3 = Boolean(required=False, allow_none=True, default=None)
    relay_4 = Boolean(required=False, allow_none=True, default=None)
