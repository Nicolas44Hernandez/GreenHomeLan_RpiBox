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
from server.orchestrator.commands import orchestrator_commands_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus


logger = logging.getLogger(__name__)


class OrchestratorRequests:
    """OrchestratorRequests service"""

    # Attributes
    def init_requests_module(
        self, mqtt_alarm_notif_topic: str, mqtt_command_topic: str
    ):
        """Initialize the requests callbacks for the orchestrator"""
        logger.info("initializing Orchestrator requests module")

        # # Set callback functions
        thread_manager_service.set_msg_reception_callback(
            self.thread_msg_reception_callback
        )

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

        logger.info(f"Thread received message: {msg} len(msg): {len(msg)}")
        try:
            # Thread message is an alarm
            if msg.startswith("al"):
                _device, _type = msg.split("_")[1:]
                if _type == "db":
                    alarm_type = "doorbell"
                elif _type == "pd":
                    alarm_type = "presence"
                elif _type == "em":
                    alarm_type = "emergency_btn"
                elif _type == "bat":  # al_bt1_bat
                    alarm_type = f"battery_btn_{_device}"
                else:
                    logger.error(f"Error in alarm received format {msg}")
                    return
                logger.info(f"Alarm received {alarm_type}")

                if _device == "cam":
                    # Turn wifi ON if alarm from camera
                    wifi_bands_manager_service.set_band_status(
                        band="2.4GHz", status=True
                    )

                # Transfer alarm to cloud server and liveobjects
                orchestrator_notification_service.transfer_alarm_to_cloud_server(
                    alarm_type
                )

            # If Thread message is buttons a command
            elif msg.startswith("cmd"):
                self.command_reception_callback(msg)

            # If Thread message is a buttons battery status command
            elif msg.startswith("bt"):
                device_type = "button"
                device, level = msg.split("_")[1:]
                logger.info(f"Device {device} battery level received: {level}")
                orchestrator_notification_service.transfer_device_battery_level_to_cloud_server(
                    device_type=device_type, device=device, batLevel=level
                )

            # If Thread message is a direct command
            else:
                if not orchestrator_commands_service.execute_command(msg):
                    logger.error("Error in command format")
                    return
        except:
            logger.error(f"Error in message received format {msg}")

    def alarm_notification_reception_callback(self, msg):
        """Callback for MQTT object alarm notification"""
        logger.info(f"Alarm notification received: {msg} ")
        orchestrator_notification_service.transfer_alarm_to_cloud_server(msg["type"])

    def command_reception_callback(self, msg):
        """Callback for MQTT command reception"""
        logger.info(f"Command received: {msg} ")
        if type(msg) == dict:
            msg = msg["command"]
        try:
            command_number = int(msg.split("cmd_")[1])
            if not orchestrator_commands_service.execute_predefined_command(
                command_number
            ):
                logger.error("Error in command format")
                return
        except:
            logger.error("Error in command format")
        logger.info("Command executed")


orchestrator_requests_service: OrchestratorRequests = OrchestratorRequests()
""" OrchestratorRequests service singleton"""
