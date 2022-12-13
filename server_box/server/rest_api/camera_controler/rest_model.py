"""REST API models for camera manager package"""

from marshmallow import Schema
from marshmallow.fields import Bool


class CameraStatusSchema(Schema):
    """REST ressource for camera status"""

    connected = Bool(required=True, allow_none=False)
