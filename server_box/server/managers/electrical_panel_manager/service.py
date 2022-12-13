import logging
from typing import Iterable
from flask import Flask
from server.interfaces.mqtt_interface import mqtt_client_interface
from datetime import datetime
from timeloop import Timeloop
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from datetime import timedelta
from server.common import ServerBoxException, ErrorCode


relays_status_timeloop = Timeloop()

logger = logging.getLogger(__name__)

# TODO:


class ElectricalPanelManager:
    """Manager for connected electrical panel"""

    mqtt_broker_address: str
    mqtt_username: str
    mqtt_password: str
    mqtt_command_relays_topic: str
    mqtt_relays_status_topic: str
    mqtt_qos: int
    mqtt_reconnection_timeout_in_secs: int
    mqtt_publish_timeout_in_secs: int
    last_relays_status_received: RelaysStatus = None

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize ElectricalPanelManager"""
        if app is not None:
            logger.info("initializing the ElectricalPanelManager")
            # Initialize configuration
            self.mqtt_broker_address = app.config["MQTT_BROKER_ADDRESS"]
            self.mqtt_username = app.config["MQTT_USERNAME"]
            self.mqtt_password = app.config["MQTT_PASSWORD"]
            self.mqtt_command_relays_topic = app.config["MQTT_COMMAND_RELAYS_TOPIC"]
            self.mqtt_relays_status_topic = app.config["MQTT_RELAYS_STATUS_TOPIC"]
            self.mqtt_qos = app.config["MQTT_QOS"]
            self.mqtt_reconnection_timeout_in_secs = app.config["MQTT_RECONNECTION_TIMEOUT_IN_SEG"]
            self.mqtt_publish_timeout_in_secs = app.config["MQTT_MSG_PUBLISH_TIMEOUT_IN_SECS"]

            # Connect to MQTT broker
            self.init_mqtt_service()

    def get_relays_last_received_status(self):
        """retrieve relays last received status and timestamp"""
        if self.last_relays_status_received is None:
            raise ServerBoxException(ErrorCode.RELAYS_STATUS_NOT_RECEIVED)
        return self.last_relays_status_received

    def get_single_relay_last_received_status(self, relay_number: int):
        """get single relay last received status"""

        if relay_number not in range(0, 6):
            raise ServerBoxException(ErrorCode.INVALID_RELAY_NUMBER)

        if self.last_relays_status_received is None:
            raise ServerBoxException(ErrorCode.RELAYS_STATUS_NOT_RECEIVED)

        for relay_status in self.last_relays_status_received.relay_statuses:
            if relay_status.relay_number == relay_number:
                return relay_status
        raise ServerBoxException(ErrorCode.RELAYS_STATUS_NOT_RECEIVED)

    def receive_relays_statuses(self, relays_status: RelaysStatus):
        """Callback for relays/status topic"""
        logger.info(f"Relays status received")

        # Update relays last status received
        relays_status.timestamp = datetime.now()
        self.last_relays_status_received = relays_status

    def publish_mqtt_relays_status_command(self, relays_status: RelaysStatus):
        """publish MQTT relays status command"""

        logger.debug(f"Publishing relays status command")
        self.mqtt_client.publish(self.mqtt_command_relays_topic, relays_status)

    def init_mqtt_service(self):
        """Connect to MQTT broker"""

        self.mqtt_client = mqtt_client_interface(
            broker_address=self.mqtt_broker_address,
            username=self.mqtt_username,
            password=self.mqtt_password,
            subscriptions={self.mqtt_relays_status_topic: self.receive_relays_statuses},
            reconnection_timeout_in_secs=self.mqtt_reconnection_timeout_in_secs,
            publish_timeout_in_secs=self.mqtt_publish_timeout_in_secs,
        )
        self.mqtt_client.connect()
        self.mqtt_client.loop_start()


electrical_panel_manager_service: ElectricalPanelManager = ElectricalPanelManager()
""" Electrical panel manager service singleton"""
