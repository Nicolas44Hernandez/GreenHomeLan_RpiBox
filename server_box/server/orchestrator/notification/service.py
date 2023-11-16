import logging
import requests
import json
from requests.exceptions import ConnectionError, InvalidURL
from typing import Iterable
from datetime import datetime
from timeloop import Timeloop
from server.managers.wifi_bands_manager.model import WifiBandStatus, WifiStatus
from server.managers.wifi_bands_manager import BANDS
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.alimelo_manager import alimelo_manager_service, AlimeloRessources
from server.managers.alimelo_manager import AlimeloRessources
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.common import ServerBoxException


logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class OrchestratorNotification:
    """OrchestratorNotification service"""

    server_cloud_notify_status_path: str
    server_cloud_notify_alarm_path: str
    server_cloud_notify_device_path: str
    server_cloud_notify_connected_nodes_path: str
    rpi_cloud_ip_addr: str
    server_cloud_ports: Iterable[int]

    def init_notification_module(
        self,
        rpi_cloud_ip_addr: str,
        server_cloud_notify_status_path: str,
        server_cloud_notify_alarm_path: str,
        server_cloud_notify_device_path: str,
        server_cloud_notify_connected_nodes_path: str,
        server_cloud_ports: Iterable[int],
    ):
        """Initialize the polling service for the orchestrator"""
        logger.info("initializing Orchestrator polling module")

        self.rpi_cloud_ip_addr = rpi_cloud_ip_addr
        self.server_cloud_notify_status_path = server_cloud_notify_status_path
        self.server_cloud_notify_alarm_path = server_cloud_notify_alarm_path
        self.server_cloud_notify_device_path = server_cloud_notify_device_path
        self.server_cloud_notify_connected_nodes_path = (
            server_cloud_notify_connected_nodes_path
        )
        self.server_cloud_ports = server_cloud_ports

    def notify_wifi_status(self, bands_status: Iterable[WifiBandStatus]):
        """Send MQTT command to electrical pannel to represent the wifi bands status"""

        logger.info("Sending MQTT message to notify wifi status")

        # Build relays command
        relays_statuses_in_command = []
        for i in range(6):
            relays_statuses_in_command.append(
                SingleRelayStatus(relay_number=i, status=False, powered=False)
            )

        for i, band in enumerate(BANDS):
            for band_status in bands_status:
                if band_status.band == band:
                    relays_statuses_in_command[i].status = band_status.status
                    relays_statuses_in_command[i].powered = band_status.status
                    break

        relays_statuses = RelaysStatus(
            relay_statuses=relays_statuses_in_command,
            command=True,
            timestamp=datetime.now(),
        )

        # Call wifi bands manager service to publish relays status command
        try:
            wifi_bands_manager_service.publish_wifi_status_mqtt_relays(
                relays_status=relays_statuses
            )
        except Exception as e:
            logger.error("Error publishing wifi status")

    def notify_cloud_server(
        self,
        bands_status: Iterable[WifiBandStatus],
        use_situation: str,
        alimelo_ressources: AlimeloRessources,
        relay_statuses: RelaysStatus,
    ):
        """Notify current wifi status and use situation to cloud server"""

        logger.info(
            "Posting HTTP to notify current wifi status and use situation to RPI cloud"
        )

        connected_to_internet = wifi_bands_manager_service.is_connected_to_internet()
        # TODO: MOCK for test REMOVE
        connected_to_internet = True
        if connected_to_internet:
            # Get wifi status from bands status
            wifi_status = False
            band_status_2GHz = False
            band_status_5GHz = False
            band_status_6GHz = False

            for band_status in bands_status:
                if band_status.band == "2.4GHz":
                    band_status_2GHz = band_status.status
                elif band_status.band == "5GHz":
                    band_status_5GHz = band_status.status
                elif band_status.band == "6GHz":
                    band_status_6GHz = band_status.status
                if band_status.status:
                    wifi_status = True

            # get Alimelo values
            alimelo_busvoltage = "unknown"
            alimelo_shuntvoltage = "unknown"
            alimelo_loadvoltage = "unknown"
            alimelo_current_mA = "unknown"
            alimelo_power_mW = "unknown"
            alimelo_battery_level = "unknown"
            alimelo_power_supplied = "unknown"
            alimelo_is_powered_by_battery = "unknown"
            alimelo_is_charging = "unknown"

            if alimelo_ressources is not None:
                alimelo_busvoltage = alimelo_ressources.busvoltage
                alimelo_shuntvoltage = alimelo_ressources.shuntvoltage
                alimelo_loadvoltage = alimelo_ressources.loadvoltage
                alimelo_current_mA = alimelo_ressources.current_mA
                alimelo_power_mW = alimelo_ressources.power_mW
                alimelo_battery_level = alimelo_manager_service.get_battery_level()
                alimelo_power_supplied = (
                    alimelo_ressources.electricSocketIsPowerSupplied
                )
                alimelo_is_powered_by_battery = alimelo_ressources.isPowredByBattery
                alimelo_is_charging = alimelo_ressources.isChargingBattery

            # Get electrical panel power outlet status
            po0_status = False
            po1_status = False
            po2_status = False
            po0_powered = False
            po1_powered = False
            po2_powered = False
            if relay_statuses is not None:
                for relay_status in relay_statuses.relay_statuses:
                    if relay_status.relay_number == 0:
                        po0_status = relay_status.status
                        po0_powered = relay_status.powered
                    if relay_status.relay_number == 1:
                        po1_status = relay_status.status
                        po1_powered = relay_status.powered
                    if relay_status.relay_number == 2:
                        po2_status = relay_status.status
                        po2_powered = relay_status.powered

            # Post status to rpi cloud
            for port in self.server_cloud_ports:
                post_url = f"http://{self.rpi_cloud_ip_addr}:{port}/{self.server_cloud_notify_status_path}"
                try:
                    headers = {"Content-Type": "application/x-www-form-urlencoded"}
                    data = {
                        "wifi_status": wifi_status,
                        "band_2GHz_status": band_status_2GHz,
                        "band_5GHz_status": band_status_5GHz,
                        "band_6GHz_status": band_status_6GHz,
                        "use_situation": use_situation,
                        "alimelo_busvoltage": alimelo_busvoltage,
                        "alimelo_shuntvoltage": alimelo_shuntvoltage,
                        "alimelo_loadvoltage": alimelo_loadvoltage,
                        "alimelo_current_mA": alimelo_current_mA,
                        "alimelo_power_mW": alimelo_power_mW,
                        "alimelo_battery_level": alimelo_battery_level,
                        "alimelo_power_supplied": alimelo_power_supplied,
                        "alimelo_is_powered_by_battery": alimelo_is_powered_by_battery,
                        "alimelo_is_charging": alimelo_is_charging,
                        "po0_status": po0_status,
                        "po0_powered": po0_powered,
                        "po1_status": po1_status,
                        "po1_powered": po1_powered,
                        "po2_status": po2_status,
                        "po2_powered": po2_powered,
                    }

                    rpi_cloud_response = requests.post(
                        post_url, data=(data), headers=headers
                    )
                    logger.info(f"RPI cloud server response: {rpi_cloud_response.text}")
                except (ConnectionError, InvalidURL):
                    logger.error(
                        f"Error when posting wifi info to rpi cloud, check if rpi cloud server is"
                        f" running"
                    )
        else:
            logger.error(
                f"Imposible to post notification, box is disconnected from internet"
            )

    def transfer_alarm_to_cloud_server(self, alarm_type: str):
        """Transfer alarm notification to cloud server"""

        connected_to_internet = wifi_bands_manager_service.is_connected_to_internet()
        # TODO: MOCK for test REMOVE
        # connected_to_internet = True
        # if connected_to_internet:
        if True:
            logger.info(f"Posting HTTP to notify alarm {alarm_type} to RPI cloud")
            data_to_send = {"alarm_type": alarm_type}
            # Post alarm to rpi cloud
            for port in self.server_cloud_ports:
                post_url = f"http://{self.rpi_cloud_ip_addr}:{port}/{self.server_cloud_notify_alarm_path}"
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

    def transfer_device_battery_level_to_cloud_server(
        self, device_type: str, device: str, batLevel: str
    ):
        """Transfer device batery level to cloud server"""
        data_to_send = {"device": device, "type": device_type, "batLevel": batLevel}
        # Post alarm to rpi cloud
        for port in self.server_cloud_ports:
            post_url = f"http://{self.rpi_cloud_ip_addr}:{port}/{self.server_cloud_notify_device_path}"
            logger.info(f"Post battery device to: {post_url}")
            try:
                headers = {"Content-Type": "application/x-www-form-urlencoded"}

                rpi_cloud_response = requests.post(
                    post_url, data=(data_to_send), headers=headers, timeout=2
                )
                logger.info(f"RPI cloud server response: {rpi_cloud_response.text}")
            except (ConnectionError, InvalidURL):
                logger.error(
                    f"Error when posting device battery level  notification to rpi cloud, check if rpi cloud"
                    f" server is running"
                )

    def notify_thread_connected_nodes_to_cloud_server(self, connected_nodes: dict):
        """Transfer connected nodes to to cloud server"""
        # Post connected nodes to rpi cloud
        data_to_send = {}
        for node_id in connected_nodes.keys():
            data_to_send[node_id] = connected_nodes[node_id].strftime("%H:%M:%S")
        for port in self.server_cloud_ports:
            post_url = f"http://{self.rpi_cloud_ip_addr}:{port}/{self.server_cloud_notify_connected_nodes_path}"
            try:
                headers = {"Content-Type": "application/x-www-form-urlencoded"}

                rpi_cloud_response = requests.post(
                    post_url, data=(data_to_send), headers=headers
                )
                logger.info(f"RPI cloud server response: {rpi_cloud_response.text}")
            except (ConnectionError, InvalidURL):
                logger.error(
                    f"Error when posting conected nodes notification to rpi cloud, check if rpi cloud"
                    f" server is running"
                )


orchestrator_notification_service: OrchestratorNotification = OrchestratorNotification()
""" OrchestratorNotification service singleton"""
