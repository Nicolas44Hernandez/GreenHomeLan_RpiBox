""" REST controller for Alimelo ressources management """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from .rest_model import AlimeloRessourcesSchema
from server.managers.alimelo_manager import alimelo_manager_service
from server.common.box_status import box_sleeping
from server.common.authentication import token_required

logger = logging.getLogger(__name__)

bp = Blueprint("alimelo", __name__, url_prefix="/alimelo")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class AlimeloRessources(MethodView):
    """API to retrieve the alimelo ressources"""

    @token_required
    @box_sleeping
    @bp.response(status_code=200, schema=AlimeloRessourcesSchema)
    def get(self):
        """Get Alimelo ressources"""
        logger.info(f"GET alimelo/")
        return alimelo_manager_service.alimelo_ressources
