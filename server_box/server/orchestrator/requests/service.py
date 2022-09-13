import logging
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.thread_manager import thread_manager_service

logger = logging.getLogger(__name__)


class OrchestratorRequests:
    """OrchestratorRequests service"""

    # Attributes
    def init_requests_module(self):
        """Initialize the requests callbacks for the orchestrator"""
        logger.info("initializing Orchestrator requests module")

        thread_manager_service.set_msg_reception_callback(self.thread_msg_reception_callback)

    def thread_msg_reception_callback(self, msg: str):
        """Callback for thread request message reception"""

        # TODO: add message format (BSON)
        logger.info(f"Thread received message: {msg}")

        try:
            # Parse received message
            ressource, band, status = msg.split("-")

            # set wifi status
            if ressource == "wifi":
                status = status == "on"
                if band == "all":
                    wifi_bands_manager_service.set_wifi_status(status=status)
                else:
                    wifi_bands_manager_service.set_band_status(band=band, status=status)
        except:
            logger.error(f"Error in message received format")
            return


orchestrator_requests_service: OrchestratorRequests = OrchestratorRequests()
""" OrchestratorRequests service singleton"""
