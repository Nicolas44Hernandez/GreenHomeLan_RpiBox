import logging
from datetime import timedelta
from timeloop import Timeloop
from server.orchestrator.notification import orchestrator_notification_service
from server.orchestrator.use_situations import orchestrator_use_situations_service
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.electrical_panel_manager import electrical_panel_manager_service

logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class OrchestratorPolling:
    """OrchestratorPolling service"""

    # Attributes
    wifi_status_polling_period_in_secs: int
    live_objects_notification_period: int

    def init_polling_module(
        self, wifi_status_polling_period_in_secs: int, live_objects_notification_period: int
    ):
        """Initialize the polling service for the orchestrator"""
        logger.info("initializing Orchestrator polling module")

        self.wifi_status_polling_period_in_secs = wifi_status_polling_period_in_secs
        self.live_objects_notification_period = live_objects_notification_period

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
            wifi_status = wifi_bands_manager_service.update_wifi_status_attribute()

            # Notify wifi status toi RPI relais
            orchestrator_notification_service.notify_wifi_status_to_rpi_relays(
                bands_status=wifi_status.bands_status
            )

            # Notify current wifi status and use situation to rpi cloud
            orchestrator_notification_service.notify_cloud_server(
                bands_status=wifi_status.bands_status,
                use_situation=orchestrator_use_situations_service.get_current_use_situation(),
            )

        # Start ressources polling and live objects notification
        @resources_status_timeloop.job(
            interval=timedelta(seconds=self.live_objects_notification_period)
        )
        def poll_ressources_and_notify_live_objects():
            # retrieve wifi status
            logger.info(f"Polling ressources status and send to LiveObjects")
            wifi_status = wifi_bands_manager_service.get_current_wifi_status()
            relay_statuses = electrical_panel_manager_service.get_relays_last_received_status()
            use_situation = orchestrator_use_situations_service.get_current_use_situation()
            connected_to_internet = wifi_bands_manager_service.is_connected_to_internet()

            # Notify wifi status and relays status to LiveObjects via Alimelo
            orchestrator_notification_service.notify_status_to_liveobjects(
                wifi_status=wifi_status,
                connected_to_internet=connected_to_internet,
                relay_statuses=relay_statuses,
                use_situation=use_situation,
            )

        resources_status_timeloop.start(block=False)


orchestrator_polling_service: OrchestratorPolling = OrchestratorPolling()
""" OrchestratorPolling service singleton"""
