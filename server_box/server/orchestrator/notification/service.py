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

    server_cloud_notify_status_path: str
    server_cloud_ports: Iterable[int]
    server_cloud_mac: str

    def init_notification_module(
        self,
        server_cloud_notify_status_path: str,
        server_cloud_mac: str,
        server_cloud_ports: Iterable[int],
    ):
        """Initialize the polling service for the orchestrator"""
        logger.info("initializing Orchestrator polling module")

        self.server_cloud_notify_status_path = server_cloud_notify_status_path
        self.server_cloud_mac = server_cloud_mac
        self.server_cloud_ports = server_cloud_ports

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

    def notify_cloud_server(self, bands_status: Iterable[WifiBandStatus], use_situation: str):
        """Notify current wifi status and use situation to cloud server"""

        logger.info("Posting HTTP to notify current wifi status and use situation to RPI cloud")

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
        for port in self.server_cloud_ports:
            post_url = f"http://{rpi_cloud_ip_addr}:{port}/{self.server_cloud_notify_status_path}"
            try:
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                data = {"wifi_status": wifi_status, "use_situation": use_situation}
                rpi_cloud_response = requests.post(post_url, data=(data), headers=headers)
                logger.info(f"RPI cloud server response: {rpi_cloud_response.text}")
            except (ConnectionError, InvalidURL):
                logger.error(
                    f"Error when posting wifi info to rpi cloud, check if rpi cloud server is"
                    f" running"
                )


orchestrator_notification_service: OrchestratorNotification = OrchestratorNotification()
""" OrchestratorNotification service singleton"""
