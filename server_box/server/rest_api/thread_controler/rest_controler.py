""" REST controller for therad network management ressource """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from .rest_model import NodeSchema
from server.managers.thread_manager import thread_manager_service
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)

bp = Blueprint("thread", __name__, url_prefix="/thread")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/setup")
class SetupThreadNetworkAllNodes(MethodView):
    """API to send the Thread network info to all the nodes in the Thread network"""

    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.response(status_code=200)
    def post(self):
        """
        Set Thread network args to all the nodes
        """
        logger.info(f"POST thread/setup")

        if not thread_manager_service.send_thread_network_info_to_all_nodes():
            raise ServerBoxException(ErrorCode.THREAD_NODE_UNREACHABLE)


@bp.route("/setup/<node>")
class SetupThreadNetworkSingleNode(MethodView):
    """API to send the Thread network info to a single node in the Thread network"""

    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.response(status_code=200)
    def post(self, node: str):
        """
        Send network info to node
        """
        logger.info(f"GET post/thread/setup/node/{node}")
        if not thread_manager_service.send_thread_network_info_to_node(node_name=node):
            raise ServerBoxException(ErrorCode.THREAD_NODE_UNREACHABLE)


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
        nodes = thread_manager_service.get_thread_nodes()
        return nodes
