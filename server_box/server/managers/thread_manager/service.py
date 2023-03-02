import logging
import threading
from datetime import timedelta, datetime
from typing import Iterable
from flask import Flask
from timeloop import Timeloop
from server.managers.mqtt_manager import mqtt_manager_service
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.interfaces.thread_interface import ThreadInterface, ThreadNode
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)

thread_network_info_timeloop = Timeloop()


class ThreadManager:
    """Manager for thread interface"""

    thread_interface: ThreadInterface
    thread_config_file: str
    mqtt_command_relays_topic: str
    publish_thread_network_info_period_in_secs: int
    nodes_check_period_in_secs: int
    nodes_keep_alive_msgs: dict

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize ThreadManager"""
        if app is not None:
            logger.info("initializing the ThreadManager")

            self.thread_config_file = app.config["THREAD_NETWORK_CONFIG"]

            self.mqtt_command_relays_topic = app.config["MQTT_THREAD_NETWORK_INFO_TOPIC"]
            self.publish_thread_network_info_period_in_secs = app.config[
                "PUBLISH_THREAD_NETWORK_PERIOD_IN_SECS"
            ]
            self.nodes_check_period_in_secs = app.config["NODES_CHECK_PERIOD_IN_SECS"]

            # setup thread interface
            self.thread_interface = ThreadInterface(
                sudo_password=app.config["SUDO_PASSWORD"],
                thread_network_config_file=self.thread_config_file,
            )
            self.thread_interface.run_dedicated_thread()

            self.thread_interface.set_keep_alive_reception_callback(
                self.keep_alive_reception_callback
            )

            # Schedule MQTT Publish Thread network info
            self.schedule_thread_management_tasks()

            self.nodes_keep_alive_msgs = {}
            for node in self.get_thread_nodes():
                self.nodes_keep_alive_msgs[node._id] = None

    def schedule_thread_management_tasks(self):
        """Schedule the thread network info publish"""

        @thread_network_info_timeloop.job(
            interval=timedelta(seconds=self.publish_thread_network_info_period_in_secs)
        )
        def publish_thread_network_info():
            logger.info(f"Publish thread netswork info to MQTT topic")
            self.publish_thread_network_info_mqtt()

        @thread_network_info_timeloop.job(
            interval=timedelta(seconds=self.nodes_check_period_in_secs)
        )
        def check_connected_nodes_keepalive_msg():
            if self.thread_interface.network_set_up_is_ok and self.thread_interface.running:
                logger.info(f"Checking thread nodes")
                reset_thread_network = False
                for node in self.get_thread_nodes():
                    last_received_keep_alive = self.nodes_keep_alive_msgs[node._id]
                    if last_received_keep_alive is None:
                        logger.error(
                            f"Haven't received keep alive message from node {node._id} in last"
                            f" {self.nodes_check_period_in_secs} secs"
                        )
                        reset_thread_network = True

                # reset to None the keep alive msgs dict
                for node in self.get_thread_nodes():
                    self.nodes_keep_alive_msgs[node._id] = None

                # Launch Thread network reset
                if reset_thread_network:
                    self.reset_thread_network()

        thread_network_info_timeloop.start(block=False)

    def reset_thread_network(self):
        """Reset therad network configuration"""
        logger.info("Reseting thread network...")
        # Turn wifi ON if necessary
        if not wifi_bands_manager_service.get_wifi_status():
            wifi_bands_manager_service.set_wifi_status(status=True)
            # Schedule WIFI OFF in 60 secs
            wifi_off_timer = threading.Timer(
                60, wifi_bands_manager_service.set_wifi_status(status=False)
            )
            wifi_off_timer.start()

        # Thread network reset
        self.thread_interface.setup_thread_network(self.thread_config_file)

    def set_msg_reception_callback(self, callback: callable):
        """Set message reception callback"""
        self.thread_interface.set_msg_reception_callback(callback)

    def keep_alive_reception_callback(self, node_id: str):
        """Callback for node keep alive reception"""
        self.nodes_keep_alive_msgs[node_id] = datetime.now()

    def publish_thread_network_info_mqtt(self) -> bool:
        """Publish network info to MQTT topic"""
        if self.thread_interface.network_set_up_is_ok and self.thread_interface.running:
            network_info = self.thread_interface.thread_network_setup
            if mqtt_manager_service.publish_message(
                topic=self.mqtt_command_relays_topic, message=network_info
            ):
                logger.info(
                    f"Network info published to MQTT topic {self.mqtt_command_relays_topic}"
                )
                # logger.info(f"Network info: {network_info}")
                return True
            else:
                logger.error(
                    "Impossible to publish network info to MQTT topic"
                    " {self.mqtt_command_relays_topic}"
                )
                return False
        else:
            logger.error("Thread network not configured or not running, tryng to setup network")
            logger.error("Message not published")
            # Launch Thread network reset
            self.reset_thread_network()

    def get_thread_nodes(self) -> Iterable[ThreadNode]:
        """return all the configured thread nodes"""
        nodes = self.thread_interface.getNodes()
        return nodes

    def get_connection_parameters(self):
        """Return thread network setup parameters"""
        try:
            return self.thread_interface.thread_network_setup
        except:
            raise ServerBoxException(ErrorCode.THREAD_NETWORK_NOT_RUNNING)


thread_manager_service: ThreadManager = ThreadManager()
""" Thread manager service singleton"""
