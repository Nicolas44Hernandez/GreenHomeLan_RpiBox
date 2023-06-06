""" REST controller for 5GHz ON/OFF management ressource """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from server.managers.wifi_5GHz_on_off_manager import wifi_5GHz_on_off_manager_service
from .rest_model import ServiceStatusSchema

logger = logging.getLogger(__name__)

bp = Blueprint("smart band manager", __name__, url_prefix="/smart_band")
""" The api blueprint. Should be registered in app main api object """

@bp.route("/")
class WifiStatusApi(MethodView):
    """API to retrieve 5GHz ON/OFF service status"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=ServiceStatusSchema)
    def get(self):
        """Get 5GHz ON/OFF service status"""
        logger.info(f"GET smart_band/")
        status = wifi_5GHz_on_off_manager_service.get_service_status()
        return {"status": status}

    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(ServiceStatusSchema, location="query")
    @bp.response(status_code=200, schema=ServiceStatusSchema)
    def post(self, args: ServiceStatusSchema):
        # TODO: use class for translate schema to object
        """
        Set 5gHz ON/OFF service status
        """
        logger.info(f"POST smart_band/")
        logger.info(f"status: {args}")

        wifi_5GHz_on_off_manager_service.set_service_status(args["status"])
        new_status = wifi_5GHz_on_off_manager_service.get_service_status()

        return {"status": new_status}
