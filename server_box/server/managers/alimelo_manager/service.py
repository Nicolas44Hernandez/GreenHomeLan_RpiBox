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
            )
            self.alimelo_interface.start()

            # set ressources notification callback
            self.alimelo_interface.set_notification_reception_callback(
                self.ressources_notification_callback
            )

    # TODO: set_live_objects_command_reception_callback

    def ressources_notification_callback(self, notification: str):
        """Ressources notification serial reception callback"""
        logger.info(f"Serial notification received :{notification}")
        alimelo_notification_dict = json.loads(notification)["alim"]
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
            rssi=alimelo_notification_dict["rssi"],
        )
        logger.info(f"alim: {alimelo_notification_dict}")


alimelo_manager_service: AlimeloManager = AlimeloManager()
""" Alimelo manager service singleton"""
