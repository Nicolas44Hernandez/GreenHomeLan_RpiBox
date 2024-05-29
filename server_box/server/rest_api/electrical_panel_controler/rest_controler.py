""" REST controller for relays management ressource """
import logging
from datetime import datetime
from flask.views import MethodView
from flask_smorest import Blueprint
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from .rest_model import SingleRelayStatusSchema, RelaysStatusResponseSchema, RelaysStatusQuerySchema
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.common.box_status import box_sleeping
from server.common.authentication import token_required
from server.common import ServerBoxException, ErrorCode


RELAYS = ["relay_0", "relay_1", "relay_2", "relay_3", "relay_4", "relay_5"]

logger = logging.getLogger(__name__)

bp = Blueprint("electrical_panel", __name__, url_prefix="/electrical_panel")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class RelaysStatusApi(MethodView):
    """API to retrieve or set electrical panel status"""

    @token_required
    @box_sleeping
    @bp.doc(
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=RelaysStatusResponseSchema)
    def get(self):
        """Get relays status"""

        logger.info(f"GET electrical_panel/")

        # Call electrical panel manager service to get relays status
        relays_status = electrical_panel_manager_service.get_relays_last_received_status()

        return relays_status

    @token_required
    @box_sleeping
    @bp.doc(responses={400: "BAD_REQUEST"})
    @bp.arguments(RelaysStatusQuerySchema, location="query")
    @bp.response(status_code=200, schema=RelaysStatusResponseSchema)
    def post(self, args: RelaysStatusQuerySchema):
        """Set relays status"""

        logger.info(f"POST relays/")
        logger.info(f"status {args}")

        # Build RelayStatus instance
        statuses_from_query = []
        for relay in RELAYS:
            if relay in args:
                statuses_from_query.append(
                    SingleRelayStatus(
                        relay_number=int(relay.split("_")[1]),
                        status=args[relay],
                        powered=args[relay],
                    ),
                )

        relays_statuses = RelaysStatus(
            relay_statuses=statuses_from_query, command=True, timestamp=datetime.now()
        )

        # Call electrical panel manager service to publish relays status command
        electrical_panel_manager_service.publish_mqtt_relays_status_command(relays_statuses)

        return relays_statuses


@bp.route("/<relay>")
class WifiBandsStatusApi(MethodView):
    """API to retrieve single relay status"""

    @token_required
    @box_sleeping
    @bp.doc(
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=SingleRelayStatusSchema)
    def get(self, relay: str):
        """Get single relay status"""

        logger.info(f"GET relays/sinle/{relay}")

        # Call electrical panel manager service to get relay status
        return electrical_panel_manager_service.get_single_relay_last_received_status(int(relay))
