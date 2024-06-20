import logging
from datetime import datetime, timedelta
from flask import Flask
from timeloop import Timeloop
from server.interfaces.thread_dongle_interface import ThreadInterface
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)

thread_network_info_timeloop = Timeloop()


class ThreadManager:
    """Manager for thread interface"""

    thread_dongle_interface: ThreadInterface
    nodes_ka_dict: dict

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize ThreadManager"""
        if app is not None:
            logger.info("initializing the ThreadManager")

            self.serial_interface = app.config["THREAD_SERIAL_INTERFACE"]
            self.serial_speed = app.config["THREAD_SERIAL_SPEED"]
            self.nodes_ka_dict = {}

            # setup thread interface
            self.thread_dongle_interface = ThreadInterface(
                thread_serial_port=self.serial_interface,
                serial_speed=self.serial_speed,
            )

            # Set keep alive callback
            self.thread_dongle_interface.set_keep_alive_reception_callback(
                self.keep_alive_reception_callback
            )

            # Run thread donfgle interface in dedicated thread
            self.thread_dongle_interface.run_dedicated_thread()

    def set_msg_reception_callback(self, callback: callable):
        """Set message reception callback"""
        self.thread_dongle_interface.set_msg_reception_callback(callback)

    def keep_alive_reception_callback(self, node_id: str):
        """Callback for node keep alive reception"""
        self.nodes_ka_dict[node_id] = datetime.now()

    def get_connected_nodes(self):
        """Return the connected nodes and the last time seen"""
        return self.nodes_ka_dict

    def update_connected_nodes(self):
        """Update connected nodes"""
        nodes_to_delete = []
        now = datetime.now()

        # Get nodes to delete
        for node in self.nodes_ka_dict:
            if self.nodes_ka_dict[node] < (now - timedelta(minutes=1)):
                nodes_to_delete.append(node)

        # Update connected nodes dictionary
        for node_to_delete_id in nodes_to_delete:
            del self.nodes_ka_dict[node_to_delete_id]

    def update_status_in_dongle(
        self,
        wifi_status: bool,
        use_situation: str,
        relay_statuses: RelaysStatus,
        power_strip_relays_statuses: RelaysStatus,
    ):
        """Update wifi and presence status in dongle"""
        logger.info(
            f"Updating status in dongle  wifi_status:{wifi_status}  use_situation:{use_situation}  pannel_relay_statuses: {relay_statuses}  power_strip: {power_strip_relays_statuses}"
        )

        # Get electricity status
        electrycity_status = False
        if relay_statuses is not None:
            for relay_status in relay_statuses.relay_statuses:
                if relay_status.relay_number in [0, 1, 2]:
                    if relay_status.status:
                        electrycity_status = True
                        break

        # Get presence status from us
        presence = "PRESENCE" in use_situation

        # Get power strip status
        msg_power_strip = self.power_strip_relays_to_str(power_strip_relays_statuses)

        # Build message
        msg_wifi = "wifi:1" if wifi_status else "wifi:0"
        msg_prs = "prs:1" if presence else "prs:0"
        msg_ele = "ele:1" if electrycity_status else "ele:0"
        message = msg_wifi + msg_prs + msg_ele + msg_power_strip
        logger.info(f"MSG: {message}")
        if not self.thread_dongle_interface.write_message_to_dongle(message):
            logger.error(f"Error sending status to dongle")

    def update_power_strip_status_in_dongle(
        self,
        power_strip_relay_statuses: RelaysStatus,
    ):
        """Update wifi and presence status in dongle"""
        logger.info(
            f"Updating power strip status in dongle  power_strip_relay_statuses: {power_strip_relay_statuses}"
        )

        if power_strip_relay_statuses is None:
            raise ServerBoxException(ErrorCode.RELAYS_STATUS_NOT_RECEIVED)

        # Format relays status to str
        msg_power_strip = self.power_strip_relays_to_str(power_strip_relay_statuses)

        logger.info(f"MSG: {msg_power_strip}")
        if not self.thread_dongle_interface.write_message_to_dongle(msg_power_strip):
            logger.error(f"Error sending status to dongle")

    def power_strip_relays_to_str(power_strip_relay_statuses: RelaysStatus):
        """Convert relays status to str to send message to thread dongle"""
        # Get power strip statuses
        r1_status = 'X'
        r2_status = 'X'
        r3_status = 'X'
        r4_status = 'X'

        for relay_status in power_strip_relay_statuses.relay_statuses:
            if relay_status.relay_number == 1:
                r1_status = '1' if relay_status.status else '0'
                continue
            if relay_status.relay_number == 2:
                r2_status = '1' if relay_status.status else '0'
                continue
            if relay_status.relay_number == 3:
                r3_status = '1' if relay_status.status else '0'
                continue
            if relay_status.relay_number == 4:
                r4_status = '1' if relay_status.status else '0'
                continue

        # Concatenate message to send
        return f"outlet:{r1_status}{r2_status}{r3_status}{r4_status}"

thread_manager_service: ThreadManager = ThreadManager()
""" Thread manager service singleton"""
