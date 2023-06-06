"""REST API models for wifi bands manager package"""

from marshmallow import Schema
from marshmallow.fields import Bool


class ServiceStatusSchema(Schema):
    """REST ressource for 5GHz on/off service status"""

    status = Bool(required=True, allow_none=False)
