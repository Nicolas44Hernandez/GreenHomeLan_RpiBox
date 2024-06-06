""" REST controller for orchestrator remote use situations management"""
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from server.managers.cameras_manager import cameras_manager_service
from .rest_model import CameraSchema
from server.common.box_status import box_sleeping
from server.common.authentication import token_required

logger = logging.getLogger(__name__)

bp = Blueprint("Remote cameras", __name__, url_prefix="/remote/cameras")
""" The api blueprint. Should be registered in app main api object """

@bp.route("/list")
class CamerasListApi(MethodView):
    """API to retrieve cameras list"""
    @token_required
    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=CameraSchema(many=True))
    def get(self):
        """Get cameras list"""
        logger.info(f"GET remote/cameras/list")
        return cameras_manager_service.get_camera_list()


@bp.route("/register")
class RegisterCameraApi(MethodView):
    """API to register a camera"""

    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(CameraSchema, location="query")
    @bp.response(status_code=200)
    def post(self, args: CameraSchema):
        """
        Register camera
        """
        logger.info(f"POST remote/cameras/register")
        cam_id = args["id"]
        cam_url = args["url"]
        logger.info(f"Registering camera    id:{cam_id} url:{cam_url}")

        cameras_manager_service.register_camera(cam_id, cam_url)
