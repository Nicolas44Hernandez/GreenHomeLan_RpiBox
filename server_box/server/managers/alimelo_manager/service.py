import logging
from flask import Flask
import json
from server.interfaces.alimelo_interface import AlimeloInterface
from .model import AlimeloRessources

logger = logging.getLogger(__name__)


class AlimeloManager:
    """Manager for Alimelo interface"""

    alimelo_interface: AlimeloInterface
    alimelo_ressources: AlimeloRessources

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize AlimeloInterface"""
        if app is not None:
            logger.info("initializing the AlimeloInterface")

            # setup alimelo interface
            self.alimelo_interface = AlimeloInterface(
                serial_port=app.config["ALIMELO_SERIAL_PORT"],
                notification_separator=app.config["ALIMELO_NOTIFICATION_SEPARATOR"],
                command_separator=app.config["ALIMELO_COMMAND_SEPARATOR"],
                serial_connection_restart_timeout_in_secs=app.config[
                    "ALIMELO_SERIAL_CONNECTION_RESTART_TIMEOUT_IN_SECS"
                ],
            )
            try:
                self.alimelo_interface.start()
            except Exception as e:
                logger.error(e)

            # Init ressources
            self.alimelo_ressources = None

            # set ressources notification callback
            self.alimelo_interface.set_notification_reception_callback(
                self.ressources_notification_callback
            )

    def set_live_objects_command_reception_callback(self, callback: callable):
        """Set command reception callback, used in the orchestrator"""
        self.alimelo_interface.set_command_reception_callback(callback=callback)

    def ressources_notification_callback(self, notification: str):
        """Ressources notification serial reception callback"""
        logger.info(f"Serial notification received :{notification}")
        # TODO: catch exception
        alimelo_notification_dict = json.loads(notification)["alimelo"]
        self.alimelo_ressources = AlimeloRessources(
            busvoltage=alimelo_notification_dict["bv"],
            shuntvoltage=alimelo_notification_dict["sw"],
            loadvoltage=alimelo_notification_dict["lv"],
            current_mA=alimelo_notification_dict["ma"],
            power_mW=alimelo_notification_dict["pw"],
            batLevel=alimelo_notification_dict["bat"],
            electricSocketIsPowerSupplied=alimelo_notification_dict["vs"],
            isPowredByBattery=alimelo_notification_dict["pb"],
            isChargingBattery=alimelo_notification_dict["ch"],
        )
        logger.info(f"alim: {alimelo_notification_dict}")

    def send_data_to_live_objects(self, data: str):
        """Send data to LiveObjects"""
        self.alimelo_interface.send_data_to_live_objects(data)

    def get_battery_level(self):
        """Get alimelo batery level in percentage"""
        if self.alimelo_ressources is None:
            return "unknown"
        return self.alimelo_ressources.batLevel - 700


alimelo_manager_service: AlimeloManager = AlimeloManager()
""" Alimelo manager service singleton"""
