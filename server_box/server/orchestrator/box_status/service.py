import server.managers.wifi_bands_manager
from server.orchestrator.use_situations import orchestrator_use_situations_service
from server.orchestrator.live_objects import live_objects_service
from server.common import ServerBoxException, ErrorCode
import logging

logger = logging.getLogger(__name__)

STATUSES = ["active", "sleep"]


class BoxStatusManager:
    """BoxStatusManager service"""

    # Attributes
    box_status: str

    def init_box_status_module(self):
        """Initialize the energy limitations module"""
        logger.info("initializing Box status module")
        self.box_status = "active"


    def get_current_box_status(self):
        """Return the current box status"""
        return self.box_status

    def send_keep_alive(self) -> bool:
        """Send keep alive message (test) to liveobjects """
        data_to_send = {"status": "running"}
        live_objects_service.publish_data(data_to_send=data_to_send, tags=["test"])
        return True

    def wakeup_box(self) -> bool:
        """Wakeup the box, return true if session token published to liveobjects """

        # Healt check
        if self.box_status == "active":
            logger.info("Box already in active status")

        # TODO: Authenticate user and generate jeton
        # MOCK: test jeton
        data_to_send = {
            "client_id": "client1",
            "token": "mock_token",
        }

        #TODO: switch use situtation from to (?)
        # try:
        #     # Activate current use situation
        #     current_use_situation = (
        #         orchestrator_use_situations_service.get_current_use_situation()
        #     )
        #     orchestrator_use_situations_service.set_use_situation(
        #         use_situation=current_use_situation
        #     )
        # except:
        #     logger.error("Error in box wakeup (use situation setting)")
        #     return False

        #TODO: wait for internet connection to send token ??
        # Publish token in liveobjects
        live_objects_service.publish_data(data_to_send=data_to_send, tags=["token"])

        return True


orchestrator_box_status_service: BoxStatusManager = BoxStatusManager()
""" Orchestrator BoxStatusManager service singleton"""
