""" REST controller for orchestrator use situation management ressource """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from server.orchestrator.use_situations import orchestrator_use_situations_service
from .rest_model import UseSituationSchema
from server.common.box_status import box_sleeping

logger = logging.getLogger(__name__)

bp = Blueprint("use_situations", __name__, url_prefix="/use_situations")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class UseSituationsListApi(MethodView):
    """API to retrieve the available current situations"""

    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200)
    def get(self):
        """Get use situation list"""
        logger.info(f"GET use_situations/")
        use_situations = orchestrator_use_situations_service.get_use_situation_list()
        return {"use_situations": use_situations}


@bp.route("/current")
class UseSituationsApi(MethodView):
    """API to retrieve and change current use situation"""

    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=UseSituationSchema)
    def get(self):
        """Get current use situation"""
        logger.info(f"GET use_situations/current")
        current_use_situation = orchestrator_use_situations_service.get_current_use_situation()
        return {"use_situation": current_use_situation}

    #TODO: Disable if box sleeping?
    # @box_sleeping
    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(UseSituationSchema, location="query")
    @bp.response(status_code=200, schema=UseSituationSchema)
    def post(self, args: UseSituationSchema):
        """
        Set current use situation
        """
        logger.info(f"POST use_situations/current")
        use_situation = args["use_situation"]
        logger.info(f"use situation: {use_situation}")
        orchestrator_use_situations_service.set_use_situation(use_situation=use_situation)

        return {"use_situation": args}
