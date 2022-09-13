import logging
import requests
from requests.exceptions import ConnectionError, InvalidURL
from typing import Iterable
from datetime import datetime
from timeloop import Timeloop
from ..model import WifiBandStatus
from server.managers.wifi_bands_manager import BANDS
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.managers.ip_discovery import ip_discovery_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.common import ServerBoxException


logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class OrchestratorNotification:
    """OrchestratorNotification service"""

    server_cloud_path: str
    server_cloud_port: int
    server_cloud_mac: str

    def init_notification_module(
        self, server_cloud_path: str, server_cloud_mac: str, server_cloud_port: int
    ):
        """Initialize the polling service for the orchestrator"""
        logger.info("initializing Orchestrator polling module")

        self.server_cloud_path = server_cloud_path
        self.server_cloud_mac = server_cloud_mac
        self.server_cloud_port = server_cloud_port

    def notify_wifi_status(self, bands_status: Iterable[WifiBandStatus]):
        """Notify current wifi status"""

        # Notify wifi status to rpi relay
        self.notify_wifi_status_to_rpi_relays(bands_status=bands_status)

        # Notify wifi status to rpi cloud
        self.notify_wifi_status_to_rpi_cloud(bands_status=bands_status)

    def notify_wifi_status_to_rpi_relays(self, bands_status: Iterable[WifiBandStatus]):
        """Send MQTT command to electrical pannel to represent the wifi bands status"""

        logger.info("Sending MQTT message to notify wifi status to RPI relays")

        # Build relays command
        relays_statuses_in_command = []
        for i, band in enumerate(BANDS):
            for band_status in bands_status:
                if band_status.band == band:
                    relays_statuses_in_command.append(
                        SingleRelayStatus(relay_number=i, status=band_status.status)
                    )
                    break

        relays_statuses = RelaysStatus(
            relay_statuses=relays_statuses_in_command, command=True, timestamp=datetime.now()
        )

        # Call electrical panel manager service to publish relays status command
        electrical_panel_manager_service.publish_mqtt_relays_status_command(relays_statuses)

    def notify_wifi_status_to_rpi_cloud(self, bands_status: Iterable[WifiBandStatus]):
        """Call HTTP post to notify wifi status to rpi cloud"""

        logger.info("Posting HTTP to notify wifi status to RPI cloud")

        # Get wifi status from bands status
        wifi_status = False
        for band_status in bands_status:
            if band_status.status:
                wifi_status = True
                break

        # get rpi cloud ip address
        try:
            rpi_cloud_ip_addr = ip_discovery_service.get_ip_addr(mac=self.server_cloud_mac)
        except ServerBoxException:
            logger.error(
                f"Error when retrieving rpi cloud ip address, check if rpi cloud server is running"
            )
            return

        # Post wifi status to rpi cloud
        post_url = f"http://{rpi_cloud_ip_addr}:{self.server_cloud_port}/{self.server_cloud_path}"
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {"status": wifi_status}
            rpi_cloud_response = requests.post(post_url, data=(data), headers=headers)
            logger.info(f"RPI cloud server response: {rpi_cloud_response.text}")
        except (ConnectionError, InvalidURL):
            logger.error(
                f"Error when posting wifi info to rpi cloud, check if rpi cloud server is running"
            )


orchestrator_notification_service: OrchestratorNotification = OrchestratorNotification()
""" OrchestratorNotification service singleton"""
