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


logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()

# TODO: logs

# TODO split orchestrator in notification - requests - polling


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
            # Initialize configuration
            self.wifi_status_polling_period_in_secs = app.config[
                "WIFI_STATUS_POLLING_PERIOD_IN_SECS"
            ]

            # Schedule ressources polling
            self.schedule_resources_status_polling()

            # Run requests reception module
            orchestrator_requests_service.init_requests_module()

    def send_relays_command(self, bands_status: Iterable[WifiBandStatus]):
        """Send MQTT command to electrical pannel to represent the wifi bands status"""

        # Build relays command
        relays_statuses_in_command = []
        for i, band in enumerate(BANDS):
            for band_status in bands_status:
                if band_status.band == band:
                    relays_statuses_in_command.append(
                        SingleRelayStatus(relay_number=i, status=band_status.status)
                    )
                    break

        relays_statuses = RelaysStatus(
            relay_statuses=relays_statuses_in_command, command=True, timestamp=datetime.now()
        )

        # Call electrical panel manager service to publish relays status command
        electrical_panel_manager_service.publish_mqtt_relays_status_command(relays_statuses)

    def schedule_resources_status_polling(self):
        """Schedule the resources polling"""

        # Start wifi status polling service
        @resources_status_timeloop.job(
            interval=timedelta(seconds=self.wifi_status_polling_period_in_secs)
        )
        def poll_wifi_status():
            # retrieve wifi status
            logger.info(f"Polling wifi status")

            status = wifi_bands_manager_service.get_wifi_status()
            bands_status = []

            for band in BANDS:
                band_status = WifiBandStatus(
                    band=band, status=wifi_bands_manager_service.get_band_status(band=band)
                )
                bands_status.append(band_status)

            self.wifi_status = WifiStatus(status=status, bands_status=bands_status)
            logger.info(f"Current wifi status: {self.wifi_status}")

            # Send relays command to electrical panel
            self.send_relays_command(bands_status=bands_status)

        resources_status_timeloop.start(block=False)


orchestrator_service: Orchestrator = Orchestrator()
""" Orchestrator service singleton"""
