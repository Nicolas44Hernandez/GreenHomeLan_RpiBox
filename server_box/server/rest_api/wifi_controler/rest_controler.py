""" REST controller for wifi bands management ressource """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from server.managers.wifi_bands_ssh_manager import wifi_bands_manager_service
from .rest_model import WifiStatusSchema, MacAdressListSchema
from server.common.box_status import box_sleeping
from server.common import ServerBoxException, ErrorCode


logger = logging.getLogger(__name__)

bp = Blueprint("wifi", __name__, url_prefix="/wifi")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class WifiStatusApi(MethodView):
    """API to retrieve wifi general status"""
    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def get(self):
        """Get livebox wifi status"""
        logger.info(f"GET wifi/")
        status = wifi_bands_manager_service.get_wifi_status()
        if status is None:
            raise ServerBoxException(ErrorCode.SSH_CONNECTION_ERROR)
        return {"status": status}

    @box_sleeping
    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(WifiStatusSchema, location="query")
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def post(self, args: WifiStatusSchema):
        # TODO: use class for translate schema to object
        """
        Set livebox wifi status
        """
        logger.info(f"POST wifi/")
        logger.info(f"status: {args}")

        new_status = wifi_bands_manager_service.set_wifi_status(args["status"])
        if new_status is None:
            raise ServerBoxException(ErrorCode.SSH_CONNECTION_ERROR)
        return {"status": new_status}


@bp.route("/bands/<band>")
class WifiBandsStatusApi(MethodView):
    """API to retrieve wifi band status"""


    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def get(self, band: str):
        """Get wifi band status"""
        logger.info(f"GET wifi/bands/{band}")

        status = wifi_bands_manager_service.get_band_status(band)
        if status is None:
            raise ServerBoxException(ErrorCode.SSH_CONNECTION_ERROR)

        return {"status": status}


    @box_sleeping
    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(WifiStatusSchema, location="query")
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def post(self, args: WifiStatusSchema, band: str):
        """
        Set wifi band status
        """
        logger.info(f"POST wifi/bands/{band}")
        logger.info(f"satus: {args}")

        new_status = wifi_bands_manager_service.set_band_status(band, args["status"])
        if new_status is None:
            raise ServerBoxException(ErrorCode.SSH_CONNECTION_ERROR)

        return {"status": new_status}


@bp.route("/stations/")
class WifiConnectedStationsApi(MethodView):
    """API to connected stations list"""


    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=MacAdressListSchema)
    def get(self):
        """Get connected stations"""
        logger.info(f"GET wifi/stations/")

        stations = wifi_bands_manager_service.get_connected_stations_mac_list()
        if stations is None:
            raise ServerBoxException(ErrorCode.SSH_CONNECTION_ERROR)

        return {"mac_list": stations}


@bp.route("/stations/<band>")
class WifiConnectedStationsApi(MethodView):
    """API to connected stations list for a band"""

    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=MacAdressListSchema)
    def get(self, band: str):
        """Get connected stations"""
        logger.info(f"GET wifi/stations/{band}")

        stations = wifi_bands_manager_service.get_connected_stations_mac_list(band)
        if stations is None:
            raise ServerBoxException(ErrorCode.SSH_CONNECTION_ERROR)

        return {"mac_list": stations}
