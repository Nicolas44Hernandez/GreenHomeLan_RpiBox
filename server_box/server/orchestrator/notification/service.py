import logging
import requests
import json
from requests.exceptions import ConnectionError, InvalidURL
from typing import Iterable
from datetime import datetime
from timeloop import Timeloop
from server.orchestrator.live_objects import live_objects_service
from server.managers.wifi_bands_manager.model import WifiBandStatus, WifiStatus
from server.managers.wifi_bands_manager import BANDS
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.alimelo_manager import alimelo_manager_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.common import ServerBoxException


logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class OrchestratorNotification:
    """OrchestratorNotification service"""

    server_cloud_notify_status_path: str
    server_cloud_notify_alarm_path: str
    rpi_cloud_ip_addr: str
    server_cloud_ports: Iterable[int]

    def init_notification_module(
        self,
        rpi_cloud_ip_addr: str,
        server_cloud_notify_status_path: str,
        server_cloud_notify_alarm_path: str,
        server_cloud_ports: Iterable[int],
    ):
        """Initialize the polling service for the orchestrator"""
        logger.info("initializing Orchestrator polling module")

        self.rpi_cloud_ip_addr = rpi_cloud_ip_addr
        self.server_cloud_notify_status_path = server_cloud_notify_status_path
        self.server_cloud_notify_alarm_path = server_cloud_notify_alarm_path
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

        # Post wifi status to rpi cloud
        for port in self.server_cloud_ports:
            post_url = (
                f"http://{self.rpi_cloud_ip_addr}:{port}/{self.server_cloud_notify_status_path}"
            )
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

    def notify_status_to_liveobjects(
        self,
        wifi_status: WifiStatus,
        connected_to_internet: bool,
        relay_statuses: RelaysStatus,
        use_situation: str,
    ):
        """Notify current status to LiveObjects"""
        logger.info(f"Notify status to Live Objects")

        # Format wifi bands status
        w = wifi_status.status
        connected_to_internet = connected_to_internet
        for band_status in wifi_status.bands_status:
            if band_status.band == "2.4GHz":
                w2 = band_status.status
            if band_status.band == "5GHz":
                w5 = band_status.status
            if band_status.band == "6GHz":
                w6 = band_status.status

        # Format electrical panel relays status
        ep = ""
        for idx in range(0, 6):
            if relay_statuses.relay_statuses[idx].status:
                ep += "1"
            else:
                ep += "0"

        # Format use situation
        us = use_situation

        data_to_send = {
            "wf": {
                "w": w,
                "ci": connected_to_internet,
                "w2": w2,
                "w5": w5,
                "w6": w6,
            },
            "ep": ep,
            "us": us,
        }
        # If connnected to internet send via internet, else send via Alimelo
        if connected_to_internet:
            live_objects_service.publish_data(topic="orch", data=data_to_send)
        else:
            data = json.dumps(data_to_send).replace(" ", "")
            alimelo_manager_service.send_data_to_live_objects(data)

    def transfer_alarm_to_cloud_server_and_liveobjects(self, alarm_type: str):
        """Transfer alarm notification to cloud server and Live objects"""
        logger.info("transfer notification")
        return

        # TODO: test send to orchestrator (mock connected to internet status and test in local)
        # TODO: test send to LO via internet et Alimelo
        connected_to_internet = wifi_bands_manager_service.is_connected_to_internet()
        data_to_send = {"alarm_type": alarm_type}

        if connected_to_internet:

            logger.info(f"Posting HTTP to notify alarm {alarm_type} to RPI cloud")
            # Post alarm to rpi cloud
            for port in self.rpi_cloud_ports:
                post_url = (
                    f"http://{self.rpi_cloud_ip_addr}:{port}/{self.server_cloud_notify_alarm_path}"
                )
                try:
                    headers = {"Content-Type": "application/x-www-form-urlencoded"}

                    rpi_cloud_response = requests.post(
                        post_url, data=(data_to_send), headers=headers
                    )
                    logger.info(f"RPI cloud server response: {rpi_cloud_response.text}")
                except (ConnectionError, InvalidURL):
                    logger.error(
                        f"Error when posting alarm notification to rpi cloud, check if rpi cloud"
                        f" server is running"
                    )

                logger.info(f"Sendig alarm {alarm_type} to LiveObjects via internet")
                live_objects_service.publish_data(topic="orch", data=data_to_send)
        else:
            data = json.dumps(data_to_send).replace(" ", "")
            alimelo_manager_service.send_data_to_live_objects(data)


orchestrator_notification_service: OrchestratorNotification = OrchestratorNotification()
""" OrchestratorNotification service singleton"""
