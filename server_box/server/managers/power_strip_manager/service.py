import logging
from flask import Flask
from server.managers.thread_manager import thread_manager_service
from datetime import datetime
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.common import ServerBoxException, ErrorCode


logger = logging.getLogger(__name__)


class PowerStripManager:
    """Manager for connected power strip"""

    relays_status: RelaysStatus = None

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize PowerStripManager"""
        if app is not None:
            logger.info("initializing the PowerStripManager")
            # Initialize configuration
            self.relays_status = None

    def get_relays_status(self):
        """return current relays status"""
        if self.relays_status is None:
            logger.error(f"The relays status have not been setted yet")
        return self.relays_status

    def get_single_relay_status(self, relay_number: int):
        """get single relay status"""

        if relay_number not in range(0, 4):
            raise ServerBoxException(ErrorCode.INVALID_RELAY_NUMBER)

        if self.relays_status is None:
            raise ServerBoxException(ErrorCode.RELAYS_STATUS_NOT_RECEIVED)

        for relay_status in self.relays_status.relay_statuses:
            if relay_status.relay_number == relay_number:
                return relay_status
        raise ServerBoxException(ErrorCode.RELAYS_STATUS_NOT_RECEIVED)

    def set_relays_statuses(self, relays_status: RelaysStatus):
        """Set relays status"""
        logger.info(f"Setting relays status to:")
        logger.info(f"{relays_status.to_json()}")

        # Update relays last status received
        relays_status.timestamp = datetime.now()
        self.relays_status = relays_status

        # Notify new status to thread dongle
        thread_manager_service.update_power_strip_status_in_dongle(power_strip_relay_statuses=self.relays_status)



power_strip_manager_service: PowerStripManager = PowerStripManager()
""" Power strio manager service singleton"""
