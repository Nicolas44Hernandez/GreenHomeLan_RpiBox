import logging
import time
from server.managers.mqtt_liveobjects_manager import mqtt_liveobjects_manager_service
from server.managers.wifi_bands_ssh_manager import wifi_bands_manager_service
from server.orchestrator.use_situations import orchestrator_use_situations_service
from server.orchestrator.live_objects import live_objects_service
from server.common.authentication import ClientsRemoteAuth
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)


class BoxStatusManager:
    """BoxStatusManager service"""

    internet_connection_timeout_in_secs: int

    def init_box_status_module(self, internet_connection_waiting_time: int):
        """Initialize the energy limitations module"""
        logger.info("initializing Box status module")
        self.internet_connection_timeout_in_secs = internet_connection_waiting_time


    def is_sleeping(self):
        """Return the current box status"""
        try:
            # Check if use situation is sleep
            current_use_situation = (
                orchestrator_use_situations_service.get_current_use_situation()
            )

            # If use situation is sleem switch it
            if current_use_situation == "DEEP_SLEEP":
                return True
            else:
                return False
        except:
            logger.error("Error in box wakeup (use situation setting)")
            return False


    def send_keep_alive(self) -> bool:
        """Send keep alive message (test) to liveobjects """
        data_to_send = {"status": "running"}
        live_objects_service.publish_data(data_to_send=data_to_send, tags=["test"])
        return True

    def wakeup_box(self) -> bool:
        """Wakeup the box, return true if session token published to liveobjects """

        # Generate token
        client_id = mqtt_liveobjects_manager_service.client_id
        logger.info(f"client_id: {client_id}")
        token = ClientsRemoteAuth.generate_token(client_id=client_id)
        logger.info(f"Token generated: {token}")

        # Generate data to send
        data_to_send = {
            "client_id": client_id,
            "token": token,
        }

        try:
            # Check if use situation is sleep
            current_use_situation = (
                orchestrator_use_situations_service.get_current_use_situation()
            )

            # If use situation is sleem switch it
            if current_use_situation == "DEEP_SLEEP":
                use_situation_to_switch = orchestrator_use_situations_service.get_use_situation_to_switch()
                orchestrator_use_situations_service.set_use_situation(
                    use_situation=use_situation_to_switch
                )
            else:
                logger.info("Box already in active status")
        except:
            logger.error("Error in box wakeup (use situation setting)")
            return False

        # Wait for internet connection
        logger.info(f"Waitting for internet connection ...")
        start = time.time()
        elapsed_time = time.time() - start
        while not wifi_bands_manager_service.is_connected_to_internet():
            elapsed_time = time.time() - start
            if elapsed_time > self.internet_connection_timeout_in_secs:
                logger.error(f"Internet connection timeout")
                return False
            time.sleep(0.5)

        # Publish token in liveobjects
        live_objects_service.publish_data(data_to_send=data_to_send, tags=["token"])

        return True


orchestrator_box_status_service: BoxStatusManager = BoxStatusManager()
""" Orchestrator BoxStatusManager service singleton"""
