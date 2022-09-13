from email.policy import default
import logging
from typing import Iterable
from flask import Flask
from datetime import datetime, timedelta
from timeloop import Timeloop
from .model import WifiBandStatus, WifiStatus
from server.managers.wifi_bands_manager import wifi_bands_manager_service, BANDS
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus
from server.orchestrator.requests import orchestrator_requests_service
from server.orchestrator.polling import orchestrator_polling_service
from server.orchestrator.notification import orchestrator_notification_service
from server.orchestrator.use_situations import orchestrator_use_situations_service


logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class Orchestrator:
    """Orchestrator service"""

    # Attributes
    wifi_status: WifiStatus

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize Orchestrator"""
        if app is not None:
            logger.info("initializing Orchestrator")

            # Init use situations module
            orchestrator_use_situations_service.init_use_situations_module(
                use_situations_config_file=app.config["USE_SITUATIONS_CONFIG"],
                default_use_situation=app.config["DEFAULT_USE_SITUATION"],
            )

            # Init notification module
            orchestrator_notification_service.init_notification_module(
                server_cloud_path=app.config["RPI_CLOUD_PATH"],
                server_cloud_mac=app.config["RPI_CLOUD_MAC"],
                server_cloud_port=app.config["RPI_CLOUD_PORT"],
            )

            # Init ressources polling module
            orchestrator_polling_service.init_polling_module(
                wifi_status_polling_period_in_secs=app.config["WIFI_STATUS_POLLING_PERIOD_IN_SECS"]
            )

            # Init requests module
            orchestrator_requests_service.init_requests_module()


orchestrator_service: Orchestrator = Orchestrator()
""" Orchestrator service singleton"""
