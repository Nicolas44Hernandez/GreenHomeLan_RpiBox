import logging
from typing import Iterable
from datetime import datetime
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.orchestrator.use_situations import orchestrator_use_situations_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus

logger = logging.getLogger(__name__)


class OrchestratorCommands:
    """OrchestratorCommands service"""

    # Attributes
    predefined_commands: dict = {}

    def init_commands_module(self, default_commands: Iterable[str]):
        """Initialize the requests callbacks for the orchestrator"""
        logger.info("initializing Orchestrator commands module")

        # Load default commands
        self.predefined_commands = default_commands

    def execute_predefined_command(self, command_number: int):
        """Execute a predefined command"""
        command_number = command_number -1
        if command_number not in range(0,len(self.predefined_commands)):
            logger.error("Error in predefined command execution")
            logger.error(f"Command {command_number} is not defined")
            return False

        # Retrieve command to execute
        command = self.predefined_commands[command_number]
        logger.info(f"Executing command: {command}")

        # Execute command
        return self.execute_command(command)

    def execute_command(self, msg: str):
        """Execute a command in the orchestrator"""
        try:
            ressource, command = msg.split("_")
        except:
            logger.error("Error in command format")
            return False

        # Execute command for requested ressource
        if ressource == "wifi":
            return self.execute_wifi_commmand(command)
        if ressource == "wifisw":
            return self.execute_wifi_switch_status_commmand()
        if ressource == "ep":
            return self.execute_electrical_pannel_commmand(command)
        if ressource == "epsw":
            return self.execute_electrical_pannel_switch_commmand(command)
        if ressource == "us":
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
                relay_statuses=statuses_from_query, command=True, timestamp=datetime.now()
            )

            # Call electrical panel manager service to publish relays status command
            electrical_panel_manager_service.publish_mqtt_relays_status_command(relays_statuses)

            logger.info(f"Electrical pannel command:  {relays_statuses}")

            return True
        except:
            logger.error("Error in electrical pannel command")
            return False

    def execute_electrical_pannel_switch_commmand(self, command: str):
        """
        Execute electrical pannel switch command, returns true if command executed
        Command format: {R0}{R1}{R2}{R3}{R4}{R5}
        """
        #TODO: retreive current relays status and switch
        logger.error("Command not already implemented")

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
        new_use_situation = orchestrator_use_situations_service.get_use_situation_to_switch()
        logger.info(f"Setting use situation: {new_use_situation}")
        try:
            orchestrator_use_situations_service.set_use_situation(use_situation=new_use_situation)
        except:
            logger.error(f"Error settting use situation {new_use_situation}")
            return False
        return True

orchestrator_commands_service: OrchestratorCommands = OrchestratorCommands()
""" OrchestratorCommands service singleton"""
