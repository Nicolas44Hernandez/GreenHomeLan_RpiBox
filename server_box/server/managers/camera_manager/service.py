import logging
from flask import Flask
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.thread_manager import thread_manager_service

logger = logging.getLogger(__name__)


class CameraManager:
    """Manager for camera"""

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize CameraManager"""
        if app is not None:
            logger.info("initializing the CameraManager")

    def camera_is_connected(self) -> bool:
        """Check if camera is connected to the livebox"""

        camera_mac_address = thread_manager_service.get_node_mac(node_name="rpi_camera")
        connected_stations = wifi_bands_manager_service.get_connected_stations_mac_list()
        for station in connected_stations:
            if station == camera_mac_address:
                return True
        return False


camera_manager_service: CameraManager = CameraManager()
""" Camera manager service singleton"""
