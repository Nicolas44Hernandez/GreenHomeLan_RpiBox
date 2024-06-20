""" REST controller for relays management ressource """
import logging
from datetime import datetime
from flask.views import MethodView
from flask_smorest import Blueprint
from server.managers.power_strip_manager import power_strip_manager_service
from .rest_model import SingleRelayStatusSchema, RelaysStatusResponseSchema, RelaysStatusQuerySchema
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.common.box_status import box_sleeping


RELAYS = ["relay_1", "relay_2", "relay_3", "relay_4"]

logger = logging.getLogger(__name__)

bp = Blueprint("power_strip", __name__, url_prefix="/power_strip")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class PowerStripStatusApi(MethodView):
    """API to retrieve or set power strip status"""

    @box_sleeping
    @bp.doc(
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=RelaysStatusResponseSchema)
    def get(self):
        """Get relays status"""

        logger.info(f"GET power_strip/")

        # Call power strip manager service to get relays status
        relays_status = power_strip_manager_service.get_relays_status()

        return relays_status

    @box_sleeping
    @bp.doc(responses={400: "BAD_REQUEST"})
    @bp.arguments(RelaysStatusQuerySchema, location="query")
    @bp.response(status_code=200, schema=RelaysStatusResponseSchema)
    def post(self, args: RelaysStatusQuerySchema):
        """Set relays status"""

        logger.info(f"POST power_strip/")
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

        # Call power strip manager service to publish relays status command
        power_strip_manager_service.set_relays_statuses(relays_status=relays_statuses)

        return relays_statuses


@bp.route("/<relay>")
class WifiBandsStatusApi(MethodView):
    """API to retrieve single relay status"""

    @box_sleeping
    @bp.doc(
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=SingleRelayStatusSchema)
    def get(self, relay: str):
        """Get single relay status"""

        logger.info(f"GET power_strip/{relay}")

        # Call electrical panel manager service to get relay status
        status = power_strip_manager_service.get_single_relay_status(relay_number=int(relay))
        return status
