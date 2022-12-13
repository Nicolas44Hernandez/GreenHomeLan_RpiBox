"""REST API models for wifi bands manager package"""

from marshmallow import Schema
from marshmallow.fields import Bool, String, List


class WifiStatusSchema(Schema):
    """REST ressource for wifi and bands status"""

    status = Bool(required=True, allow_none=False)


class MacAdressListSchema(Schema):
    """Rest ressource for mac addresses list"""

    mac_list = List(String, required=True)
