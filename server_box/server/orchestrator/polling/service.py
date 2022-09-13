import logging
from typing import Iterable
from datetime import datetime, timedelta
from timeloop import Timeloop
from server.orchestrator.model import WifiBandStatus, WifiStatus
from server.orchestrator.notification import orchestrator_notification_service
from server.managers.wifi_bands_manager import wifi_bands_manager_service, BANDS
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.interfaces.mqtt_interface import SingleRelayStatus, RelaysStatus

logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class OrchestratorPolling:
    """OrchestratorPolling service"""

    # Attributes
    wifi_status_polling_period_in_secs: int

    def init_polling_module(self, wifi_status_polling_period_in_secs: int):
        """Initialize the polling service for the orchestrator"""
        logger.info("initializing Orchestrator polling module")

        self.wifi_status_polling_period_in_secs = wifi_status_polling_period_in_secs
        # Schedule ressources polling
        self.schedule_resources_status_polling()

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

            # Notify wifi status
            orchestrator_notification_service.notify_wifi_status(bands_status=bands_status)

        resources_status_timeloop.start(block=False)


orchestrator_polling_service: OrchestratorPolling = OrchestratorPolling()
""" OrchestratorPolling service singleton"""
