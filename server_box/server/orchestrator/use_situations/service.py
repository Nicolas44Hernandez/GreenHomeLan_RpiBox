import logging
import yaml
from datetime import datetime
from timeloop import Timeloop
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.common import ServerBoxException, ErrorCode


logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class OrchestratorUseSituations:
    """OrchestratorUseSituations service"""

    use_situations_dict: dict
    current_use_situation: str

    def init_use_situations_module(
        self, use_situations_config_file: str, default_use_situation: str
    ):
        """Initialize the use situations  service for the orchestrator"""
        logger.info("initializing Orchestrator use situations module")

        # Load use situations from copnfig
        self.load_use_situations(use_situations_config_file)

        # set default use situation
        self.set_use_situation(use_situation=default_use_situation)

    def load_use_situations(self, use_situations_config_file: str):
        """load the use situations from config"""
        logger.info("Use situations config file: %s", use_situations_config_file)

        # Load Use situations configuration
        with open(use_situations_config_file) as stream:
            try:
                configuration = yaml.safe_load(stream)
                self.use_situations_dict = {}
                for situation in configuration["USE_SITUATIONS"]:
                    self.use_situations_dict[situation] = configuration[
                        "USE_SITUATIONS"
                    ][situation]
            except (yaml.YAMLError, KeyError) as exc:
                raise ServerBoxException(ErrorCode.USE_SITUATIONS_CONFIG_FILE_ERROR)

    def set_use_situation(self, use_situation: str):
        """Set use situation"""
        logger.info(f"Setting use situation: {use_situation}")
        if use_situation in self.use_situations_dict:
            self.current_use_situation = use_situation
        else:
            logger.error(f"Invalid use situation")
            self.current_use_situation = None
            raise ServerBoxException(ErrorCode.INVALID_USE_SITUATION)

        # Set use situation wifi status
        self.set_use_situation_wifi_status(
            self.use_situations_dict[self.current_use_situation]["WIFI"]
        )

        # Set use situation Electrical panel
        self.set_use_situation_electrical_panel_status(
            self.use_situations_dict[self.current_use_situation]["ELECTRICAL_OUTLETS"]
        )

    def set_use_situation_wifi_status(self, wifi_bands_status: dict):
        """Set wifi status"""
        for band in wifi_bands_status:
            band_status = wifi_bands_status[band]
            logger.info(f"Setting wifi band {band} to {band_status}")
            ret = wifi_bands_manager_service.set_band_status(
                band=band, status=band_status
            )
            if ret is None:
                logger.error("Error in wifi band status command execution")
                return False

    def set_use_situation_electrical_panel_status(self, electrical_panel_status: dict):
        """Set electrical panel status"""
        # Build RelayStatus instance
        relays_status = []
        for outlet_number in range(6):
            if outlet_number in electrical_panel_status:
                outlet_status = electrical_panel_status[outlet_number]
            else:
                outlet_status = False
            logger.info(f"Setting power outlet {outlet_number} to {outlet_status}")
            relays_status.append(
                SingleRelayStatus(
                    relay_number=outlet_number,
                    status=outlet_status,
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

    def get_current_use_situation(self):
        """Get current use situation"""
        return self.current_use_situation

    def get_use_situation_list(self):
        """Get available use situation list"""
        return list(self.use_situations_dict.keys())

    def get_use_situation_to_switch(self):
        """Get the use situation to switch for command"""
        return self.use_situations_dict[self.current_use_situation]["SWITCH_TO"]


orchestrator_use_situations_service: OrchestratorUseSituations = (
    OrchestratorUseSituations()
)
""" OrchestratorUseSituations service singleton"""
