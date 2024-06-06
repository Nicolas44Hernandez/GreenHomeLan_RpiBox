import logging
from typing import Iterable
from flask import Flask
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)


class CamerasManager:
    """Manager for cameras"""

    secret_key: str
    cameras: dict

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize CamerasManager"""
        if app is not None:
            logger.info("initializing the CamerasManager")

            # Initialize configuration
            self.secret_key = app.config["SECRET_KEY"]
            self.cameras = {}

    def register_camera(self, _id: int, url):
        """Register camera in list"""
        # Register / update camera url
        self.cameras[_id] = url

        logger.info(f"Camera registered id:{_id} url:{url}")
        return

    def get_secret_key(self):
        """Return orchestrator secret key for token decrypt"""
        return self.secret_key

    def get_camera_list(self):
        """Return camera list"""
        camera_list = []
        for cam_id in self.cameras:
            camera_list.append({"id": cam_id, "url": self.cameras[cam_id]})

        return camera_list

cameras_manager_service: CamerasManager = CamerasManager()
""" Cameras manager service singleton"""
