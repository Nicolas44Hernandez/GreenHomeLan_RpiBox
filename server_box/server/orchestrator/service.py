import logging
from flask import Flask
from timeloop import Timeloop
from server.orchestrator.requests import orchestrator_requests_service
from server.orchestrator.polling import orchestrator_polling_service
from server.orchestrator.notification import orchestrator_notification_service
from server.orchestrator.use_situations import orchestrator_use_situations_service
from server.orchestrator.commands import orchestrator_commands_service


logger = logging.getLogger(__name__)

resources_status_timeloop = Timeloop()


class Orchestrator:
    """Orchestrator service"""

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize Orchestrator"""
        if app is not None:
            logger.info("initializing Orchestrator")

            # Init use situations module
            # orchestrator_use_situations_service.init_use_situations_module(
            #     use_situations_config_file=app.config["USE_SITUATIONS_CONFIG"],
            #     default_use_situation=app.config["DEFAULT_USE_SITUATION"],
            # )

            # Init notification module
            orchestrator_notification_service.init_notification_module(
                rpi_cloud_ip_addr=app.config["RPI_CLOUD_IP"],
                server_cloud_notify_status_path=app.config[
                    "RPI_CLOUD_NOTIFY_STATUS_PATH"
                ],
                server_cloud_notify_alarm_path=app.config[
                    "RPI_CLOUD_NOTIFY_ALARM_PATH"
                ],
                server_cloud_notify_device_path=app.config["RPI_CLOUD_DEVICE_PATH"],
                server_cloud_notify_connected_nodes_path=app.config[
                    "RPI_CLOUD_THREAD_NODES_PATH"
                ],
                server_cloud_ports=app.config["RPI_CLOUD_PORTS"],
            )

            # Init ressources polling module
            orchestrator_polling_service.init_polling_module(
                wifi_status_polling_period_in_secs=app.config[
                    "WIFI_STATUS_POLLING_PERIOD_IN_SECS"
                ],
                alimelo_status_check_period_in_secs=app.config[
                    "ALIMELO_STATUS_CHECK_PERIOD_IN_SECS"
                ],
                connected_thread_nodes_notification_period_in_secs=app.config[
                    "THREAD_NODES_CHECK_PERIOD_IN_SECS"
                ],
                home_office_mac_addr=app.config["HOME_OFFICE_MAC_ADDR"],
            )

            # Init requests module
            # orchestrator_requests_service.init_requests_module(
            #     mqtt_alarm_notif_topic=app.config["MQTT_ALARM_NOTIFICATION_TOPIC"],
            #     mqtt_command_topic=app.config["MQTT_COMMAND_TOPIC"]
            # )

            # Init commands module
            orchestrator_commands_service.init_commands_module(
                orchestrator_commands_file=app.config["ORCHESTRATOR_COMMANDS"]
            )


orchestrator_service: Orchestrator = Orchestrator()
""" Orchestrator service singleton"""
