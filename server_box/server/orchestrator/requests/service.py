import logging
import json
from datetime import datetime
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.thread_manager import thread_manager_service
from server.managers.alimelo_manager import alimelo_manager_service
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.orchestrator.use_situations import orchestrator_use_situations_service
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
            cmd_dict = alimelo_command_dict["cmd"]
            ressource = alimelo_command_dict["ress"]

            # Wifi command
            if ressource == "wifi":
                wifi_general_status = None
                wifi_band_2GHz = None
                wifi_band_5GHz = None
                wifi_band_6GHz = None
                if "all" in cmd_dict.keys():
                    wifi_general_status = cmd_dict["all"]
                if "2GHz" in cmd_dict.keys():
                    wifi_band_2GHz = cmd_dict["2GHz"]
                if "5GHz" in cmd_dict.keys():
                    wifi_band_5GHz = cmd_dict["5GHz"]
                if "6GHz" in cmd_dict.keys():
                    wifi_band_6GHz = cmd_dict["6GHz"]

                logger.info(
                    f"Wifi command  w={wifi_general_status}  w2={wifi_band_2GHz} "
                    f" w5={wifi_band_5GHz}  w6={wifi_band_6GHz}"
                )
                if wifi_general_status is not None:
                    wifi_bands_manager_service.set_wifi_status(status=wifi_general_status)
                else:
                    if wifi_band_2GHz is not None:
                        wifi_bands_manager_service.set_band_status(
                            band="2.4GHz", status=wifi_band_2GHz
                        )
                    if wifi_band_5GHz is not None:
                        wifi_bands_manager_service.set_band_status(
                            band="5GHz", status=wifi_band_5GHz
                        )
                    if wifi_band_6GHz is not None:
                        wifi_bands_manager_service.set_band_status(
                            band="6GHz", status=wifi_band_6GHz
                        )

            # Electrical pannel command
            if ressource == "electrical_panel":
                statuses_from_query = []
                for relay_idx in cmd_dict.keys():
                    relay_status = cmd_dict[relay_idx]
                    statuses_from_query.append(
                        SingleRelayStatus(relay_number=int(relay_idx), status=relay_status),
                    )

                relays_statuses = RelaysStatus(
                    relay_statuses=statuses_from_query, command=True, timestamp=datetime.now()
                )

                # Call electrical panel manager service to publish relays status command
                electrical_panel_manager_service.publish_mqtt_relays_status_command(relays_statuses)

                logger.info(f"Electrical pannel command:  {relays_statuses}")

            # Use situation command
            if ressource == "use_situations":
                new_use_situation = cmd_dict["use_situation"]
                logger.info(f"Setting use situation: {new_use_situation}")
                orchestrator_use_situations_service.set_use_situation(
                    use_situation=new_use_situation
                )

        except (Exception, ValueError) as e:
            logger.error(f"Error in message received format")
            return


orchestrator_requests_service: OrchestratorRequests = OrchestratorRequests()
""" OrchestratorRequests service singleton"""
