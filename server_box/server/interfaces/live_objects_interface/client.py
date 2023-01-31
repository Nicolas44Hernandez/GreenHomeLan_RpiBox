import logging
import time
from typing import TypeVar
import LiveObjects


logger = logging.getLogger(__name__)

Msg = TypeVar("Msg")


class LiveObjectsClient:
    """Service class for Live Objects client"""

    lo: LiveObjects
    command_reception_callback: callable
    notification_reception_callback: callable

    def __init__(self):
        """Class to manage message reception and sent to Live Objects"""
        self.connect()
        self.lo.loop

    def connect(self):
        """Connect to broker, retry if connection unsuccessful"""
        # TODO: Manage reconnection to LO
        try:
            self.lo = LiveObjects.Connection()
            self.lo.add_command("orchestrator", self.message_reception_callback)
            self.lo.connect()
        except Exception as e:
            logger.exception("Connection to Live Objects unsuccessful")
            logger.info("Retrying connection ...")
            time.sleep(10)
            return self.connect()

    def message_reception_callback(self, arg={}):
        logger.info("Message received")
        is_command = arg["command"]
        try:
            if is_command:
                self.command_reception_callback(arg["cmd"])
            else:
                self.notification_reception_callback(arg["notification"])
        except:
            logger.exception("Error in message received format")
        return {}

    def set_command_reception_callback(self, callback: callable):
        """Set Live Objects command reception callback"""
        self.command_reception_callback = callback

    def set_notification_reception_callback(self, callback: callable):
        """Set Live Objects notification reception callback"""
        self.notification_reception_callback = callback

    def disconnect(self):
        """Send disconnection message to broker"""

        logger.info("Disconnect from broker")
        self.lo.disconnect()

    def publish(
        self,
        topic: str,
        message: Msg,
    ):
        """
        Try to publish a message to Live Objects
        """

        logger.info(f"Trying to publish message  {message} to topic {topic}")
        try:
            self.lo.add_to_payload(topic, message)
            self.lo.send_data()
        except Exception as e:
            logger.exception(f"Error when tryng to publish message to Live Objects")
            return False
        return True
