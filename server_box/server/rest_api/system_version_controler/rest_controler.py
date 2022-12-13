""" REST controller for system version ressource """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from .rest_model import SystemVersionSchema
from server.managers.wifi_bands_manager import wifi_bands_manager_service

logger = logging.getLogger(__name__)

bp = Blueprint("system_version", __name__, url_prefix="/system_version")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/<module>")
class ModuleVersionApi(MethodView):
    """API to retrieve system version"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=SystemVersionSchema)
    def get(self, module: str):
        """Get module version"""
        version = wifi_bands_manager_service.get_module_version(module)

        return {"version": version}
