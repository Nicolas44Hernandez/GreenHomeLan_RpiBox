import logging
import json
from datetime import datetime
from server.managers.wifi_bands_manager import wifi_bands_manager_service

from server.managers.thread_manager import thread_manager_service
from server.managers.mqtt_manager import mqtt_manager_service
from server.managers.alimelo_manager import alimelo_manager_service
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.orchestrator.use_situations import orchestrator_use_situations_service
from server.orchestrator.notification import orchestrator_notification_service
from server.orchestrator.live_objects import live_objects_service
from server.orchestrator.commands import orchestrator_commands_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus


logger = logging.getLogger(__name__)


class OrchestratorRequests:
    """OrchestratorRequests service"""

    # Attributes
    def init_requests_module(self, mqtt_alarm_notif_topic: str, mqtt_command_topic: str):
        """Initialize the requests callbacks for the orchestrator"""
        logger.info("initializing Orchestrator requests module")

        # # Set callback functions
        thread_manager_service.set_msg_reception_callback(self.thread_msg_reception_callback)

        # alimelo_manager_service.set_live_objects_command_reception_callback(
        #     self.live_objects_command_reception_callback
        # )

        # live_objects_service.set_commands_reception_callback(
        #     self.live_objects_command_reception_callback
        # )

        # live_objects_service.set_notifications_reception_callback(
        #     self.live_objects_notification_reception_callback
        # )

        # Subscribe to command reception MQTT topic
        logger.info(f"Subscribe to MQTT topic: {mqtt_command_topic}")
        mqtt_manager_service.subscribe_to_topic(
            topic=mqtt_command_topic,
            callback=self.command_reception_callback,
        )

        # Subscribe to alarm notification MQTT topic
        logger.info(f"Subscribe to MQTT topic: {mqtt_alarm_notif_topic}")
        mqtt_manager_service.subscribe_to_topic(
            topic=mqtt_alarm_notif_topic,
            callback=self.alarm_notification_reception_callback,
        )

    def thread_msg_reception_callback(self, msg: str):
        """Callback for thread request message reception"""

        # TODO: add message format (BSON)
        logger.info(f"Thread received message: {msg}")

        # Thread message is an alarm
        if msg.startswith("al"):
            _device, _type = msg.split("_")[1:]
            if _type == "db":
                alarm_type = "doorbell"
            elif _type == "pd":
                alarm_type = "presence"
            elif _type == "em":
                alarm_type = "emergency_btn"
            else:
                logger.error(f"Error in alarm received format {msg}")
                return
            logger.info(f"Alarm received {alarm_type}")

            if _device == "cam":
                # Turn wifi ON if alarm from camera
                wifi_bands_manager_service.set_band_status(band="5GHz", status=True)

            # Transfer alarm to cloud server and liveobjects
            orchestrator_notification_service.transfer_alarm_to_cloud_server_and_liveobjects(
                alarm_type
            )

        # If Thread message is buttons a command
        elif msg.startswith("cmd"):
            self.command_reception_callback(msg)

        # If Thread message is a direct wifi command
        else:
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
                logger.error(f"Error in message received format {msg}")

    def live_objects_command_reception_callback(self, command: str):
        """Callback for alimelo command reception"""

        logger.info(f"Live Objects received command: {command}")

        try:
            if type(command) is dict:
                alimelo_command_dict = command
            else:
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
                        SingleRelayStatus(
                            relay_number=int(relay_idx), status=relay_status, powered=True
                        ),
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

    def live_objects_notification_reception_callback(self, notification: str):
        """Callback for alimelo notification reception"""

        logger.info(f"Live objects received notification: {notification}")
        # TODO: What to do with notifications

    def alarm_notification_reception_callback(self, msg):
        """Callback for MQTT object alarm notification"""
        logger.info(f"Alarm notification received: {msg} ")
        orchestrator_notification_service.transfer_alarm_to_cloud_server_and_liveobjects(
            msg["type"]
        )

    def command_reception_callback(self, msg):
        """Callback for MQTT command reception"""
        logger.info(f"Command received: {msg} ")
        if type(msg) == dict:
            msg = msg["command"]
        try:
            command_number = int(msg.split("cmd_")[1])
            if not orchestrator_commands_service.execute_predefined_command(command_number):
                logger.error("Error in command format")
                return
        except:
            logger.error("Error in command format")
        logger.info("Command executed")

orchestrator_requests_service: OrchestratorRequests = OrchestratorRequests()
""" OrchestratorRequests service singleton"""
