""" REST controller for wifi bands management ressource """
from ast import Str
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from .rest_model import WifiStatusSchema, MacAdressListSchema

logger = logging.getLogger(__name__)

bp = Blueprint("wifi", __name__, url_prefix="/wifi")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class WifiStatusApi(MethodView):
    """API to retrieve wifi general status"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def get(self):
        """Get livebox wifi status"""
        logger.info(f"GET wifi/")
        status = wifi_bands_manager_service.get_wifi_status()
        return {"status": status}

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

        return {"status": new_status}


@bp.route("/bands/<band>")
class WifiBandsStatusApi(MethodView):
    """API to retrieve wifi band status"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=WifiStatusSchema)
    def get(self, band: str):
        """Get wifi band status"""
        logger.info(f"GET wifi/bands/{band}")

        status = wifi_bands_manager_service.get_band_status(band)

        return {"status": status}

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

        return {"status": new_status}


@bp.route("/stations/")
class WifiConnectedStationsApi(MethodView):
    """API to connected stations list"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=MacAdressListSchema)
    def get(self):
        """Get connected stations"""
        logger.info(f"GET wifi/stations/")

        stations = wifi_bands_manager_service.get_connected_stations_mac_list()

        return {"mac_list": stations}


@bp.route("/stations/<band>")
class WifiConnectedStationsApi(MethodView):
    """API to connected stations list for a band"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=MacAdressListSchema)
    def get(self, band: str):
        """Get connected stations"""
        logger.info(f"GET wifi/stations/{band}")

        stations = wifi_bands_manager_service.get_connected_stations_mac_list(band)

        return {"mac_list": stations}
