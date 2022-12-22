import logging
import json
from datetime import datetime
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.thread_manager import thread_manager_service
from server.managers.alimelo_manager import alimelo_manager_service
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus


logger = logging.getLogger(__name__)


class OrchestratorRequests:
    """OrchestratorRequests service"""

    # Attributes
    def init_requests_module(self):
        """Initialize the requests callbacks for the orchestrator"""
        logger.info("initializing Orchestrator requests module")

        # Set callback functions
        thread_manager_service.set_msg_reception_callback(self.thread_msg_reception_callback)

        alimelo_manager_service.set_live_objects_command_reception_callback(
            self.alimelo_command_reception_callback
        )

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

    def alimelo_command_reception_callback(self, command: str):
        """Callback for alimelo command reception"""

        logger.info(f"Alimelo received command: {command}")

        try:
            alimelo_command_dict = json.loads(command)["cmd"]

            for ressource in alimelo_command_dict.keys():
                # Wifi command
                if ressource == "wf":
                    wifi_general_status = alimelo_command_dict[ressource]["w"]
                    wifi_band_2GHz = alimelo_command_dict[ressource]["w2"]
                    wifi_band_5GHz = alimelo_command_dict[ressource]["w5"]
                    wifi_band_6GHz = alimelo_command_dict[ressource]["w6"]
                    logger.info(
                        f"Wifi command  w={wifi_general_status}  w2={wifi_band_2GHz} "
                        f" w5={wifi_band_5GHz}  w6={wifi_band_6GHz}"
                    )
                    if not wifi_general_status:
                        wifi_bands_manager_service.set_wifi_status(status=wifi_general_status)
                    else:
                        wifi_bands_manager_service.set_band_status(
                            band="2.4GHz", status=wifi_band_2GHz
                        )
                        wifi_bands_manager_service.set_band_status(
                            band="5GHz", status=wifi_band_5GHz
                        )
                        wifi_bands_manager_service.set_band_status(
                            band="6GHz", status=wifi_band_6GHz
                        )

                # Electrical pannel command
                if ressource == "ep":
                    statuses_from_query = []
                    relays_status_cmd = alimelo_command_dict[ressource]
                    for idx, relay_status_str in enumerate(reversed((relays_status_cmd))):
                        relay_status = relay_status_str == "1"
                        statuses_from_query.append(
                            SingleRelayStatus(relay_number=idx, status=relay_status),
                        )

                    relays_statuses = RelaysStatus(
                        relay_statuses=statuses_from_query, command=True, timestamp=datetime.now()
                    )

                    # Call electrical panel manager service to publish relays status command
                    electrical_panel_manager_service.publish_mqtt_relays_status_command(
                        relays_statuses
                    )

                    logger.info(f"Electrical pannel command:  {relays_statuses}")

        except (Exception, ValueError) as e:  # TODO: review possible exceptions
            logger.error(f"Error in message received format")
            return


orchestrator_requests_service: OrchestratorRequests = OrchestratorRequests()
""" OrchestratorRequests service singleton"""
