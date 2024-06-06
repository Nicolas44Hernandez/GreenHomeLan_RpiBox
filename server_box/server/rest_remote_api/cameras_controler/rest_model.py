
from marshmallow import Schema
from marshmallow.fields import String, Integer, Nested, List


class CameraSchema(Schema):
    """REST ressource for single camera"""

    id = Integer(required=True, allow_none=False, data_key='_id')
    url = String(required=True, allow_none=False)
