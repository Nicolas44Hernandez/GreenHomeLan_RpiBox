import logging
import subprocess
import urllib.request
from typing import Iterable
from flask import Flask
import yaml
import time
from datetime import datetime, timedelta
from telnetlib import Telnet
from server.interfaces.box_interface_telnet import box_telnet_interface
from server.interfaces.mqtt_interface import RelaysStatus
from server.managers.mqtt_manager import mqtt_manager_service
from server.common import ServerBoxException, ErrorCode
from .model import WifiBandStatus, WifiStatus


logger = logging.getLogger(__name__)

BANDS = ["2.4GHz", "5GHz", "6GHz"]
STATUS_CHANGE_TIMEOUT_IN_SECS = 15


class WifiBandsManager:
    """Manager for wifi control"""

    livebox_ip_address: str = None
    livebox_telnet_port: int = 23
    livebox_login: str = None
    livebox_password: str = None
    telnet_timeout_in_secs: float = 5
    telnet_commands = {}
    wifi_status: WifiStatus = None
    mqtt_wifi_status_relays_topic: str
    last_counter_rxbytes: int
    last_counter_txbytes: int
    last_counter_datetime: datetime

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize WifiBandsManager"""
        if app is not None:
            logger.info("initializing the WifiBandsManager")
            # Initialize configuration
            self.livebox_ip_address = app.config["LIVEBOX_IP_ADDRESS"]
            self.livebox_telnet_port = app.config["LIVEBOX_TELNET_PORT"]
            self.livebox_login = app.config["LIVEBOX_LOGIN"]
            self.livebox_ip_password = app.config["LIVEBOX_PASSWORD"]
            self.telnet_timeout_in_secs = app.config["TELNET_TIMOUT_IN_SECS"]
            self.mqtt_wifi_status_relays_topic = app.config[
                "MQTT_WIFI_STATUS_RELAYS_TOPIC"
            ]
            self.load_telnet_commands(app.config["LIVEBOX_TELNET_COMMANDS"])

    def create_telnet_connection(self) -> Telnet:
        """Create wifi telnet interface object for telnet commands"""
        # Create telnet connection
        return box_telnet_interface(
            host=self.livebox_ip_address,
            port=self.livebox_telnet_port,
            login=self.livebox_login,
            password=self.livebox_ip_password,
            telnet_timeout_in_secs=self.telnet_timeout_in_secs,
        )

    def load_telnet_commands(self, commands_yaml_file: str):
        """Load the telnet commands dict from file"""
        logger.info("Telnet commands file: %s", commands_yaml_file)
        # Load logging configuration and configure flask application logger
        with open(commands_yaml_file) as stream:
            try:
                self.telnet_commands = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                raise ServerBoxException(ErrorCode.COMMANDS_FILE_ERROR)

    def execute_telnet_commands(
        self, dictionary_keys: Iterable[str], station_mac: str = None
    ):
        """
        Create a telnet connection and execute a command or a group of commands
        in telnet host
        """
        # Retreive commands
        new_element = self.telnet_commands
        for key in dictionary_keys:
            try:
                new_element = new_element[key]
            except:
                logger.error(
                    "Item not found in tenlet commands: ", str[dictionary_keys]
                )
                raise ServerBoxException(ErrorCode.COMMAND_NOT_FOUND)

        commands = new_element

        # If the command retrieved is not a str or a list command is wrong
        if not isinstance(commands, (str, list)):
            raise ServerBoxException(ErrorCode.COMMAND_NOT_FOUND)

        # create telnet connection
        telnet = self.create_telnet_connection()

        if isinstance(commands, str):
            # replace station mac if needed
            if station_mac and "STATION" in commands:
                commands = commands.replace("STATION", station_mac)
            # Execute telnet comand
            output = telnet.send_command(commands)

        elif isinstance(commands, list):
            # used for in pcb_cli commands
            in_pcb_cli = False

            output = []
            # Loop over commands list
            for command in commands:
                # Execute telnet comand
                if in_pcb_cli:
                    command_output = telnet.send_fast_command(command=command)
                else:
                    command_output = telnet.send_command(command=command)

                output.append(command_output)

                if "pcb_cli" in command:
                    in_pcb_cli = True

        # Close telnet connection
        telnet.close()

        # return command.s output
        return output

    def get_wifi_status(self):
        """Execute get wifi status command in the livebox using telnet service"""
        try:
            commands_response = self.execute_telnet_commands(["WIFI", "status"])
        except:
            return None

        wifi_status = True if "up" in commands_response else False
        return wifi_status

    def set_wifi_status(self, status: bool):
        """Execute set wifi status command in the livebox using telnet service"""

        # set max duration timmer
        start = datetime.now()
        status_change_timeout = start + timedelta(seconds=STATUS_CHANGE_TIMEOUT_IN_SECS)

        # check if requested status is already satisfied
        current_wifi_status = self.get_wifi_status()
        if current_wifi_status is None:
            return None
        if current_wifi_status == status:
            return current_wifi_status

        # execute wifi status change command
        try:
            self.execute_telnet_commands(["WIFI", status])
        except ServerBoxException:
            return None

        # set max duration timmer
        now = datetime.now()
        status_change_timeout = now + timedelta(seconds=STATUS_CHANGE_TIMEOUT_IN_SECS)

        # Waiting loop
        status_change_trys = 0
        while now < status_change_timeout:
            current_wifi_status = self.get_wifi_status()
            if current_wifi_status is status:
                return current_wifi_status
            time.sleep(0.2)
            now = datetime.now()
            status_change_trys += 1

        raise ServerBoxException(ErrorCode.STATUS_CHANGE_TIMER)

    def get_band_status(self, band: str):
        """Execute get wifi band status command in the livebox using telnet service"""
        # Check if band number exists
        if band not in BANDS:
            raise ServerBoxException(ErrorCode.UNKNOWN_BAND_WIFI)

        try:
            commands_response = self.execute_telnet_commands(
                ["WIFI", "bands", band, "status"]
            )
        except ServerBoxException as e:
            logger.error(e.message)
            return None
        if not commands_response:
            band_status = False
        else:
            band_status = True if "up" in commands_response else False
        return band_status

    def set_band_status(self, band: str, status: bool):
        """Execute set wifi band status command in the livebox using telnet service"""
        # Check if the band exists
        if band not in BANDS:
            raise ServerBoxException(ErrorCode.UNKNOWN_BAND_WIFI)

        # set max duration timmer
        start = datetime.now()
        status_change_timeout = start + timedelta(seconds=STATUS_CHANGE_TIMEOUT_IN_SECS)

        # check if requested status is already satisfied
        current_band_status = self.get_band_status(band)
        if current_band_status is None:
            logger.error("Error when getting band status")
            return None
        if current_band_status == status:
            return current_band_status

        # execute wifi status change command
        try:
            self.execute_telnet_commands(["WIFI", "bands", band, status])
        except ServerBoxException as e:
            logger.error(e.message)
            return None

        # set max duration timmer
        now = datetime.now()
        status_change_timeout = now + timedelta(seconds=STATUS_CHANGE_TIMEOUT_IN_SECS)

        # Waiting loop
        status_change_trys = 0
        while now < status_change_timeout:
            current_band_status = self.get_band_status(band)
            if current_band_status is status:
                return current_band_status
            time.sleep(0.2)
            now = datetime.now()
            status_change_trys += 1
        logger.error(f"Wifi status change is taking too long, verify wifi status")

    def get_connected_stations_mac_list(self, band=None) -> Iterable[str]:
        """Execute get connected stations in the livebox using telnet service"""
        connected_stations = []

        # if band is None return all the connected stations
        if band is None:
            for band in BANDS:
                try:
                    _stations = self.execute_telnet_commands(
                        ["WIFI", "bands", band, "stations"]
                    ).split("assoclist")
                except ServerBoxException as e:
                    logger.error(e.message)
                    return None
                for station in _stations:
                    if len(station) > 5:
                        station = " ".join(station.split())
                        connected_stations.append(station)
            return connected_stations

        # Check if the band exists
        if band is not None and band not in BANDS:
            raise ServerBoxException(ErrorCode.UNKNOWN_BAND_WIFI)

        # return stations connected to the band
        connected_stations = []

        try:
            _stations = self.execute_telnet_commands(
                ["WIFI", "bands", band, "stations"]
            ).split("assoclist")
        except ServerBoxException as e:
            logger.error(e.message)
            return None

        for station in _stations:
            if len(station) > 12:
                station = " ".join(station.split())
                connected_stations.append(station)
        return connected_stations

    def update_wifi_status_attribute(self) -> WifiStatus:
        """Retrieve wifi status and update wifi_status attribute"""
        status = self.get_wifi_status()
        if status is None:
            return None
        bands_status = []

        for band in BANDS:
            band_status = WifiBandStatus(
                band=band, status=wifi_bands_manager_service.get_band_status(band=band)
            )
            if band_status is None:
                return None
            bands_status.append(band_status)

        self.wifi_status = WifiStatus(status=status, bands_status=bands_status)
        return self.wifi_status

    def get_current_wifi_status(self) -> WifiStatus:
        """Retrieve current wifi² status"""
        return self.wifi_status

    def is_connected_to_internet(self) -> bool:
        """Check internet connection"""
        try:
            urllib.request.urlopen("http://google.com")
            return True
        except:
            return False

    def publish_wifi_status_mqtt_relays(self, relays_status: RelaysStatus):
        """publish MQTT relays status command"""

        logger.debug(f"Publishing relays status command")
        mqtt_manager_service.publish_message(
            topic=self.mqtt_wifi_status_relays_topic, message=relays_status
        )


wifi_bands_manager_service: WifiBandsManager = WifiBandsManager()
""" Wifi manager service singleton"""