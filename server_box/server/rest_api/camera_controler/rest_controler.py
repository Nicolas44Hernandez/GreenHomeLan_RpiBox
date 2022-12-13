""" REST controller for Camera management ressource """
from ast import Str
import logging
from flask.views import MethodView
from flask_smorest import Blueprint

from server.managers.camera_manager import camera_manager_service
from .rest_model import CameraStatusSchema

logger = logging.getLogger(__name__)

bp = Blueprint("camera", __name__, url_prefix="/camera")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class CameraStatusApi(MethodView):
    """API to retrieve camera connection status"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=CameraStatusSchema)
    def get(self):
        """Get camera connection status"""
        logger.info(f"GET camera/")
        connection_status = camera_manager_service.camera_is_connected()
        return {"connected": connection_status}
