import logging
from typing import Iterable
import yaml
from datetime import datetime
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.orchestrator.use_situations import orchestrator_use_situations_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus

logger = logging.getLogger(__name__)

BANDS = ["2.4GHz", "5GHz", "6GHz"]


class OrchestratorCommands:
    """OrchestratorCommands service"""

    # Attributes
    current_commands: dict = {}
    commands_dict: dict = {}

    def init_commands_module(self, orchestrator_commands_file: str):
        """Initialize the requests callbacks for the orchestrator"""
        logger.info("initializing Orchestrator commands module")
        self.commands_dict = {}
        self.current_commands = {}

        # Load commands file
        with open(orchestrator_commands_file) as stream:
            try:
                configuration = yaml.safe_load(stream)
                for command in configuration["COMMANDS_LIST"]:
                    self.commands_dict[command["id"]] = {
                        "name": command["name"],
                        "command": command["command"],
                    }

                # Set predefined commands
                for idx, command_id in enumerate(configuration["DEFAULT_COMMANDS"]):
                    command = self.commands_dict[command_id]
                    command["id"] = command_id
                    self.current_commands[idx] = command

            except (yaml.YAMLError, KeyError):
                logger.error(
                    "Error in orchestrator commands configuration load, check file"
                )

            logger.info(f"current commands: {self.current_commands}")

    def execute_predefined_command(self, command_number: int):
        """Execute a predefined command"""
        command_number = command_number - 1
        if command_number not in self.current_commands:
            logger.error("Error in predefined command execution")
            logger.error(f"Command {command_number} is not defined")
            return False

        # Retrieve command to execute
        command = self.current_commands[command_number]["command"]
        logger.info(f"Executing command: {command}")

        # Execute command
        return self.execute_command(command)

    def execute_command(self, msg: str):
        """Execute a command in the orchestrator"""
        try:
            logger.info(f"Executing command: {msg}")
            msg = str(msg)
            ressource, command = msg.split("_")
        except:
            logger.error("Error in command format")
            return False

        # Execute command for requested ressource
        if ressource == "wifi":
            return self.execute_wifi_commmand(command)
        if ressource == "wifisw":
            return self.execute_wifi_switch_status_commmand()
        if ressource == "wifiswb":
            return self.execute_wifi_switch_band_status_commmand(command)
        if ressource == "ep":
            return self.execute_electrical_pannel_commmand(command)
        if ressource == "epsw":
            return self.execute_electrical_pannel_switch_commmand()
        if ressource == "resw":
            return self.execute_relay_switch_commmand(command)
        if ressource == "us":
            command = command.replace("-", "_")
            return self.execute_use_situations_commmand(command)
        if ressource == "prs":
            return self.execute_presence_commmand()

        logger.error("Error in command format")
        return False

    def execute_wifi_commmand(self, command: str):
        """
        Execute wifi command, returns true if command executed
        Command format {band}_{status}
        """
        try:
            band, status = command.split("-")

            status = status == "on"
            if band == "all":
                wifi_bands_manager_service.set_wifi_status(status=status)
            else:
                wifi_bands_manager_service.set_band_status(band=band, status=status)
            return True
        except:
            logger.error("Error in wifi command format")
            return False

    def execute_wifi_switch_status_commmand(self):
        """
        Execute wifi switch status command, returns true if command executed
        If current status is ON set OFF
        If current status is OFF set ON
        """

        current_wifi_status = wifi_bands_manager_service.get_current_wifi_status()
        try:
            wifi_bands_manager_service.set_wifi_status(not current_wifi_status.status)
            return True
        except:
            logger.error("Error in wifi status command execution")
            return False

    def execute_wifi_switch_band_status_commmand(self, band: str):
        """
        Execute wifi switch band status command, returns true if command executed
        If band current status is ON set OFF
        If band current status is OFF set ON
        """
        # Check band exists
        if band not in BANDS:
            logger.error(f"Error, the band {band} doesnt exist")
            return False
        current_wifi_band_status = wifi_bands_manager_service.get_band_status(band)

        try:
            wifi_bands_manager_service.set_band_status(
                band=band, status=not current_wifi_band_status
            )
            return True
        except:
            logger.error("Error in wifi status command execution")
            return False

    def execute_electrical_pannel_commmand(self, command: str):
        """
        Execute electrical pannel command, returns true if command executed
        Command format: {R0}{R1}{R2}{R3}{R4}{R5}
        """
        if len(command) != 6:
            logger.error("Error in electrical pannel command")
            return False

        statuses_from_query = []

        try:
            for relay_idx, relay_status_char in enumerate(command):
                relay_status = relay_status_char == "1"
                statuses_from_query.append(
                    SingleRelayStatus(
                        relay_number=int(relay_idx), status=relay_status, powered=True
                    ),
                )
            relays_statuses = RelaysStatus(
                relay_statuses=statuses_from_query,
                command=True,
                timestamp=datetime.now(),
            )

            # Call electrical panel manager service to publish relays status command
            electrical_panel_manager_service.publish_mqtt_relays_status_command(
                relays_statuses
            )

            logger.info(f"Electrical pannel command:  {relays_statuses}")

            return True
        except:
            logger.error("Error in electrical pannel command")
            return False

    def execute_electrical_pannel_switch_commmand(self):
        """
        Execute electrical pannel switch command, returns true if command executed
        """
        relays_statuses = (
            electrical_panel_manager_service.get_relays_last_received_status().relay_statuses
        )
        new_status = True
        for relay_status in relays_statuses:
            if relay_status.status:
                new_status = False
                break

        if new_status:
            orchestrator_use_situations_service.set_use_situation_electrical_panel_status(
                orchestrator_use_situations_service.use_situations_dict[
                    orchestrator_use_situations_service.current_use_situation
                ]["ELECTRICAL_OUTLETS"]
            )
            return True
        else:
            return self.execute_electrical_pannel_commmand("000000")

    def execute_relay_switch_commmand(self, command: str):
        """
        Execute sinfgle relay switch command, returns true if command executed
        Command format: {R#}
        """
        relay_number = int(command)
        relay_status = (
            electrical_panel_manager_service.get_single_relay_last_received_status(
                relay_number
            ).status
        )
        new_status = not relay_status

        # Build RelayStatus instance
        relays_status = []
        for relay_nb in range(6):
            relay_status = (
                electrical_panel_manager_service.get_single_relay_last_received_status(
                    relay_nb
                ).status
            )

            if relay_nb == relay_number:
                new_status = not relay_status
            else:
                new_status = relay_status
            relays_status.append(
                SingleRelayStatus(
                    relay_number=relay_nb,
                    status=new_status,
                    powered=False,
                ),
            )

        relays_statuses = RelaysStatus(
            relay_statuses=relays_status, command=True, timestamp=datetime.now()
        )
        logger.info(f"{relays_statuses.to_json()}")

        # Call electrical panel manager service to publish relays status command
        electrical_panel_manager_service.publish_mqtt_relays_status_command(
            relays_statuses
        )

    def execute_use_situations_commmand(self, command: str):
        """
        Execute use situations command, returns true if command executed
        Command format: {USE_SITUATION}
        """

        new_use_situation = command
        logger.info(f"Setting use situation: {new_use_situation}")
        try:
            orchestrator_use_situations_service.set_use_situation(
                use_situation=new_use_situation
            )
        except:
            logger.error("Error in use situations command")
            return False
        return True

    def execute_presence_commmand(self):
        """
        Execute presence command, returns true if command executed
        """
        new_use_situation = (
            orchestrator_use_situations_service.get_use_situation_to_switch()
        )
        logger.info(f"Setting use situation: {new_use_situation}")
        try:
            orchestrator_use_situations_service.set_use_situation(
                use_situation=new_use_situation
            )
        except:
            logger.error(f"Error settting use situation {new_use_situation}")
            return False
        return True

    def get_commands_list(self):
        """Get commands list"""
        commands_list = [
            {"id": command_id, "name": self.commands_dict[command_id]["name"]}
            for command_id in self.commands_dict
        ]
        return commands_list

    def get_current_commands(self):
        """Get current commands"""
        current_commands_list = [
            {
                "id": self.current_commands[command_id]["id"],
                "name": self.current_commands[command_id]["name"],
            }
            for command_id in self.current_commands
        ]
        return current_commands_list

    def set_commands(self, commands_id_list: Iterable[int]):
        """Set new current commmands from an id list, returns True if commands correctly setted"""
        # Check that args are ok
        if len(commands_id_list) != len(self.current_commands):
            logger.error(f"Error setting commands {commands_id_list}")
            return False

        # Check that all the received ids match a command in the list
        for received_id in commands_id_list:
            if received_id not in self.commands_dict:
                logger.error(
                    f"Error setting commands, command {received_id} doesnt exist"
                )
                return False

        # Set new commands
        for idx, command_id in enumerate(commands_id_list):
            command = self.commands_dict[command_id]
            command["id"] = command_id
            self.current_commands[idx] = command

        return True


orchestrator_commands_service: OrchestratorCommands = OrchestratorCommands()
""" OrchestratorCommands service singleton"""
