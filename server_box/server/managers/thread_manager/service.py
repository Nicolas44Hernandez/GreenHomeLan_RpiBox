import logging
from datetime import datetime
from flask import Flask
from timeloop import Timeloop
from server.interfaces.thread_interface import ThreadInterface
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)

thread_network_info_timeloop = Timeloop()


class ThreadManager:
    """Manager for thread interface"""

    thread_interface: ThreadInterface
    thread_config_file: str
    nodes_ka_dict: dict

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize ThreadManager"""
        if app is not None:
            logger.info("initializing the ThreadManager")

            self.thread_config_file = app.config["THREAD_NETWORK_CONFIG"]
            self.nodes_ka_dict = {}

            # setup thread interface
            self.thread_interface = ThreadInterface(
                sudo_password=app.config["SUDO_PASSWORD"],
                thread_network_config_file=self.thread_config_file,
            )
            self.thread_interface.run_dedicated_thread()

            self.thread_interface.set_keep_alive_reception_callback(
                self.keep_alive_reception_callback
            )

    def set_msg_reception_callback(self, callback: callable):
        """Set message reception callback"""
        self.thread_interface.set_msg_reception_callback(callback)

    def keep_alive_reception_callback(self, node_id: str):
        """Callback for node keep alive reception"""
        self.nodes_ka_dict[node_id] = datetime.now()

    def get_connection_parameters(self):
        """Return thread network setup parameters"""
        try:
            return self.thread_interface.thread_network_setup
        except:
            raise ServerBoxException(ErrorCode.THREAD_NETWORK_NOT_RUNNING)

    def get_connected_nodes(self):
        """Return the connected nodes and the last time seen"""
        return self.nodes_ka_dict

thread_manager_service: ThreadManager = ThreadManager()
""" Thread manager service singleton"""
