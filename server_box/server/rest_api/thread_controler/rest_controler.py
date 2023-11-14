""" REST controller for therad network management ressource """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from .rest_model import NodeSchema, ThreadNetworkSetupSchema
from server.managers.thread_manager import thread_manager_service

logger = logging.getLogger(__name__)

bp = Blueprint("thread", __name__, url_prefix="/thread")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/nodes")
class ThreadNodesApi(MethodView):
    """API to retrieve thread configured nodes"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=NodeSchema(many=True))
    def get(self):
        """Get configured thread nodes"""
        logger.info(f"GET thread/nodes")
        nodes = thread_manager_service.get_connected_nodes()
        resp = []
        for node_id in nodes.keys():
            resp.append(
                {"id": node_id, "last_seen": nodes[node_id].strftime("%H:%M:%S")}
            )
        return resp
