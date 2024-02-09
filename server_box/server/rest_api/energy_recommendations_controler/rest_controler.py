""" REST controller for orchestrator energy recommendations management ressource """

import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from server.orchestrator.energy_limitations import (
    orchestrator_energy_limitations_service,
)
from .rest_model import EnergyRecommendationSchema

logger = logging.getLogger(__name__)

bp = Blueprint("energy_recomendations", __name__, url_prefix="/energy_recomendations")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/current_limitation")
class UseSituationsListApi(MethodView):
    """API to retrieve the orchestratpr current energy limitation"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200)
    def get(self):
        """Get orchestrator current energy limitation"""
        logger.info(f"GET energy_recomendations/current_limitation/")
        energy_limitation = (
            orchestrator_energy_limitations_service.get_current_energy_limitations()
        )
        return {"energy_limitation": energy_limitation}


@bp.route("/")
class UseSituationsApi(MethodView):
    """API to post energy recommendaiton"""

    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(EnergyRecommendationSchema, location="query")
    @bp.response(status_code=200)
    def post(self, args: EnergyRecommendationSchema):
        """
        Post energy recommendation
        """
        logger.info(f"POST energy_recomendations")
        logger.info(f"Recommendation: {args}")

        # TODO: code for start_datetime and end_datetime
        start_datetime = None
        end_datetime = None

        orchestrator_energy_limitations_service.manage_energy_recommendation(
            recomendation_datetime=args["recomendation_datetime"],
            sender=args["sender"],
            msg_id=args["msg_id"],
            msg_title=args["msg_title"],
            id_zone=args["id_zone"],
            id_energy_supplier=args["id_energy_supplier"],
            recommendation_class=args["recommendation_class"],
            power=args["power"],
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
