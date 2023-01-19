"""REST API models for Alimelo package"""

from marshmallow import Schema
from marshmallow.fields import Float, Bool, Integer


class AlimeloRessourcesSchema(Schema):
    """REST ressource for Alimelo ressources"""

    busvoltage = Float(required=True, allow_none=False)
    shuntvoltage = Float(required=True, allow_none=False)
    loadvoltage = Float(required=True, allow_none=False)
    current_mA = Float(required=True, allow_none=False)
    power_mW = Float(required=True, allow_none=False)
    batLevel = Float(required=True, allow_none=False)
    electricSocketIsPowerSupplied = Bool(required=True, allow_none=False)
    isPowredByBattery = Bool(required=True, allow_none=False)
    isChargingBattery = Bool(required=True, allow_none=False)
