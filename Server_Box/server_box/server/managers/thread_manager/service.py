import logging
from typing import Iterable
from flask import Flask
import requests
from requests.exceptions import ConnectionError

from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.interfaces.thread_interface import ThreadInterface, ThreadNode
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)


class ThreadManager:
    """Manager for thread interface"""

    thread_interface: ThreadInterface

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize ThreadManager"""
        if app is not None:
            logger.debug("initializing the ThreadManager")

            # TODO: Veryfy that WIFI is ON before continue otherwise turn it on

            # setup thread interface
            self.thread_interface = ThreadInterface(
                sudo_password=app.config["SUDO_PASSWORD"],
                thread_network_config_file=app.config["THREAD_NETWORK_CONFIG"],
            )
            # TODO: Verify thread dependency on main thread
            self.thread_interface.start()
            # self.thread_interface.join()

            # Send thread network info to all nodes in config
            if not self.send_thread_network_info_to_all_nodes():
                logger.error("Eror when posting network info to thread nodes")

    def set_msg_reception_callback(self, callback: callable):
        """Set message reception callback"""
        self.thread_interface.set_msg_reception_callback(callback)

    def send_thread_network_info_to_node(self, node_name: str) -> bool:
        """send thread network config to node return False if error in post"""

        dest_node: ThreadNode = None
        for node in self.thread_interface.getNodes():
            if node.name == node_name:
                dest_node = node
                break

        # Sanity check
        if dest_node is None:
            raise ServerBoxException(ErrorCode.THREAD_NODE_NOT_CONFIGURED)

        # send network info to node server
        # TODO: is there a way to get the IP Automatically knowing the MAC?
        try:
            node_response = requests.post(
                dest_node.url, json=self.thread_interface.thread_network_setup
            )
            logger.debug(f"Node server response: {node_response.text}")
            return True
        except ConnectionError:
            logger.error(
                f"Error when posting network info to thread node {dest_node.name}, check if node"
                " server is running"
            )
            return False

    def send_thread_network_info_to_all_nodes(self) -> bool:
        """send thread network config to all the nodes"""
        for node in self.thread_interface.getNodes():
            if not self.send_thread_network_info_to_node(node.name):
                return False
        return True

    def get_thread_nodes(self) -> Iterable[ThreadNode]:
        """return all the configured thread nodes"""
        nodes = self.thread_interface.getNodes()
        return nodes

    def get_node_mac(self, node_name: str):
        """return the mac node address"""
        node_to_find: ThreadNode = None
        for node in self.thread_interface.getNodes():
            if node.name == node_name:
                node_to_find = node
                break

        # Sanity check
        if node_to_find is None:
            raise ServerBoxException(ErrorCode.THREAD_NODE_NOT_CONFIGURED)

        return node_to_find.mac


thread_manager_service: ThreadManager = ThreadManager()
""" Thread manager service singleton"""
