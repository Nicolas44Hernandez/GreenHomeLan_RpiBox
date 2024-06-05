"""REST API models for the Orchestrator remote APIs package"""

from marshmallow import Schema
from marshmallow.fields import String


class UseSituationSchema(Schema):
    """REST ressource orchestrator use situations"""

    use_situation = String(required=True, allow_none=False)
