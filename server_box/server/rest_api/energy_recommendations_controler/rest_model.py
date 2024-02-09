"""REST API models for the orchestrator energy recommendations package"""

from marshmallow import Schema
from marshmallow.fields import String, DateTime


class EnergyRecommendationSchema(Schema):
    recomendation_datetime = DateTime(
        required=True,
        allow_none=False,
        example="2024-01-22T13:47:33+0000",
    )
    sender = String(required=True, allow_none=False, example="PIE")
    msg_id = String(required=True, allow_none=False, example="0003")
    msg_title = String(required=True, allow_none=False, example="Msg title")
    id_zone = String(required=True, allow_none=False, example="35NNE")
    id_energy_supplier = String(required=True, allow_none=False, example="E1")
    recommendation_class = String(required=True, allow_none=False, example="6KVA")
    start_datetime = DateTime(
        required=False,
        example="2024-01-22T13:47:33+0000",
    )
    end_datetime = DateTime(
        required=False,
        allow_none=False,
        example="2024-01-22T13:49:33+0000",
    )
    power = String(required=True, allow_none=False, example="25")
