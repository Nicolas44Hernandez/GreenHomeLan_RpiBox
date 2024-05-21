""" REST controller for Remote client ressources """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from server.common.authentication import token_required
from server.common.box_status import box_sleeping
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.rest_api.wifi_controler.rest_model import WifiStatusSchema
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)

bp = Blueprint("remote wifi", __name__, url_prefix="/remote/wifi")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class RemoteWifiStatusApi(MethodView):
    """API to retrieve wifi general status from remote"""
    @token_required
    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def get(self):
        """Get livebox wifi status"""
        logger.info(f"GET wifi/  (REMOTE)")
        status = wifi_bands_manager_service.get_wifi_status()
        if status is None:
            raise ServerBoxException(ErrorCode.TELNET_CONNECTION_ERROR)
        return {"status": status}

    @token_required
    @box_sleeping
    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(WifiStatusSchema, location="query")
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def post(self, args: WifiStatusSchema):
        """
        Set livebox wifi status
        """
        logger.info(f"POST wifi/  (REMOTE)")
        logger.info(f"status: {args}")

        new_status = wifi_bands_manager_service.set_wifi_status(args["status"])
        if new_status is None:
            raise ServerBoxException(ErrorCode.TELNET_CONNECTION_ERROR)
        return {"status": new_status}


@bp.route("/bands/<band>")
class RemoteWifiBandsStatusApi(MethodView):
    """API to retrieve wifi band status from remote"""

    @token_required
    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def get(self, band: str):
        """Get wifi band status"""
        logger.info(f"GET wifi/bands/{band}  (REMOTE)")

        status = wifi_bands_manager_service.get_band_status(band)
        if status is None:
            raise ServerBoxException(ErrorCode.TELNET_CONNECTION_ERROR)

        return {"status": status}

    @token_required
    @box_sleeping
    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(WifiStatusSchema, location="query")
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def post(self, args: WifiStatusSchema, band: str):
        """
        Set wifi band status
        """
        logger.info(f"POST wifi/bands/{band} (REMOTE)")
        logger.info(f"satus: {args}")

        new_status = wifi_bands_manager_service.set_band_status(band, args["status"])
        if new_status is None:
            raise ServerBoxException(ErrorCode.TELNET_CONNECTION_ERROR)

        return {"status": new_status}
