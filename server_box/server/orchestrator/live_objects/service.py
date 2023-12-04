import logging
from server.interfaces.live_objects_interface import live_objects_client_interface

logger = logging.getLogger(__name__)


class LiveObjects:
    # TODO: manage Live Objects disconnection
    # TODO: What to do if cant connect to Live objects (continue and try if required)

    live_objects_interface: live_objects_client_interface

    def init_live_objects_module(self) -> None:
        # Interface to connect to Live Objects
        self.live_objects_interface = live_objects_client_interface()

    def set_notifications_reception_callback(self, callback: callable):
        """Set callback for notifications reception"""
        self.live_objects_interface.set_notification_reception_callback(callback)

    def set_commands_reception_callback(self, callback: callable):
        """Set callback for commabnds reception"""
        self.live_objects_interface.set_command_reception_callback(callback)

    def publish_data(self, topic: str, data: str):
        """publish data to Live Objects"""

        logger.debug(f"Publishing data to Live Objects")
        self.live_objects_interface.publish(topic, data)


live_objects_service: LiveObjects = LiveObjects()
