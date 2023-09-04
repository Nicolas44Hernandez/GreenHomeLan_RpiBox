import logging
from datetime import timedelta
from timeloop import Timeloop
from server.orchestrator.notification import orchestrator_notification_service
from server.orchestrator.use_situations import orchestrator_use_situations_service
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.thread_manager import thread_manager_service
from server.managers.electrical_panel_manager import electrical_panel_manager_service
from server.managers.alimelo_manager import alimelo_manager_service, AlimeloRessources

logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class OrchestratorPolling:
    """OrchestratorPolling service"""

    # Attributes
    wifi_status_polling_period_in_secs: int
    live_objects_notification_period: int
    wifi_counters_polling_period_in_secs: int
    alimelo_status_check_period_in_secs: int
    connected_thread_nodes_notification_period_in_secs: int
    home_office_mac_addr: str

    def init_polling_module(
        self,
        wifi_status_polling_period_in_secs: int,
        live_objects_notification_period: int,
        wifi_counters_polling_period_in_secs: int,
        alimelo_status_check_period_in_secs: int,
        connected_thread_nodes_notification_period_in_secs: int,
        home_office_mac_addr: str,
    ):
        """Initialize the polling service for the orchestrator"""
        logger.info("initializing Orchestrator polling module")

        self.wifi_status_polling_period_in_secs = wifi_status_polling_period_in_secs
        self.live_objects_notification_period = live_objects_notification_period
        self.connected_thread_nodes_notification_period_in_secs = connected_thread_nodes_notification_period_in_secs
        self.wifi_counters_polling_period_in_secs = wifi_counters_polling_period_in_secs
        self.alimelo_status_check_period_in_secs = alimelo_status_check_period_in_secs
        self.home_office_mac_addr = home_office_mac_addr

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
            connected_stations = (
                wifi_bands_manager_service.get_connected_stations_mac_list()
            )
            if self.home_office_mac_addr in connected_stations:
                logger.info(
                    f"Home office PC connectedf, setting use situation PRESENCE_HOME_OFFICE"
                )
                orchestrator_use_situations_service.set_use_situation(
                    use_situation="PRESENCE_HOME_OFFICE"
                )

            # Notify wifi status toi RPI relais
            orchestrator_notification_service.notify_wifi_status(
                bands_status=wifi_status.bands_status
            )
            logger.info(f"Polling wifi: RPI relas wifi notification ok")

            # Notify current wifi status and use situation to rpi cloud
            orchestrator_notification_service.notify_cloud_server(
                bands_status=wifi_status.bands_status,
                use_situation=orchestrator_use_situations_service.get_current_use_situation(),
                alimelo_ressources=alimelo_manager_service.alimelo_ressources,
                relay_statuses=electrical_panel_manager_service.get_relays_last_received_status(),
            )
            logger.info(f"Polling wifi done")

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

        @resources_status_timeloop.job(
            interval=timedelta(seconds=self.connected_thread_nodes_notification_period_in_secs)
        )
        def notify_thread_connected_nodes_to_cloud():
            # retrieve connected nodes
            logger.info(f"Polling thread connected nodes and notify cloud")
            connected_nodes = thread_manager_service.get_connected_nodes()

            # Notify connected nodes to cloud
            orchestrator_notification_service.notify_thread_connected_nodes_to_cloud_server(
                connected_nodes=connected_nodes
            )



        # @resources_status_timeloop.job(
        #     interval=timedelta(seconds=self.alimelo_status_check_period_in_secs)
        # )
        # def check_alimelo_status():
        #     """Check alimelo rssources status, if necessary manage wifi ressources"""
        #     logger.info("CHECK ALIMELO STATUS")
        #     if alimelo_manager_service.alimelo_ressources is not None:
        #         # Get alimelo ressources to evaluate
        #         alimelo_vs = (
        #             alimelo_manager_service.alimelo_ressources.electricSocketIsPowerSupplied
        #         )
        #         bat_level = alimelo_manager_service.get_battery_level()

        #         # if electric socket is not power supplied and low battery level, send alarm
        #         if not alimelo_vs and bat_level < 10:
        #             logger.info("Alimelo low power alarm")
        #             orchestrator_notification_service.transfer_alarm_to_cloud_server_and_liveobjects(
        #                 alarm_type="low_power"
        #             )

        resources_status_timeloop.start(block=False)


orchestrator_polling_service: OrchestratorPolling = OrchestratorPolling()
""" OrchestratorPolling service singleton"""
