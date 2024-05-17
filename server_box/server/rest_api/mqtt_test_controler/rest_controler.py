""" REST controller for MQTT test (liveobjects and local brokers) """
import logging
from flask.views import MethodView
from flask_smorest import Blueprint
from server.orchestrator.live_objects import live_objects_service
from server.orchestrator.box_status import orchestrator_box_status_service
from server.managers.mqtt_manager import mqtt_manager_service

logger = logging.getLogger(__name__)

bp = Blueprint("mqtt", __name__, url_prefix="/mqtt")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/liveobjects")
class TestLiveObjectsMQTTApi(MethodView):
    """API to send a test message to liveobjects"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200)
    def get(self):
        """Get use situation list"""
        logger.info(f"GET mqtt/liveobjects")
        orchestrator_box_status_service.wakeup_box()
        #live_objects_service.publish_data(data_to_send={"client_id": "client1","token": "test_token"}, tags=["test"])


@bp.route("/test_local_broker_msg")
class TestLocalMQTTApi(MethodView):
    """API to send a test message to liveobjects"""

    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200)
    def get(self):
        """Send message to local broker"""
        logger.info(f"GET mqtt/local")
        mqtt_manager_service.publish_message(
            topic="command/relays", message={"data":"relays_status_test"}
        )


