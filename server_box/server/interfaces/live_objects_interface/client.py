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
    connected: bool
    max_connection_retries: int

    def __init__(self):
        """Class to manage message reception and sent to Live Objects"""
        self.max_connection_retries = 2
        if self.connect(self.max_connection_retries):
            self.lo.loop

    def connect(self, remaining_attempts) -> bool:
        """Connect to broker, retry if connection unsuccessful"""
        self.connected = False
        logger.info("Triyng to connect to LiveObjects server.")
        try:
            self.lo = LiveObjects.Connection()
            self.lo.add_command("orchestrator", self.message_reception_callback)
            self.lo.connect()
            self.connected = True
            return True
        except Exception as e:
            logger.error(
                "Connection to Live Objects unsuccessful, retrying connection ..."
            )
            self.disconnect()
            logger.error(f"Remaining reconnection attemps {remaining_attempts}")
            if remaining_attempts > 0:
                time.sleep(1)
                return self.connect(remaining_attempts - 1)
            else:
                logger.error(f"Connection impossible")
                self.connected = False
                return False

    def message_reception_callback(self, arg={}):
        logger.info("Message received")
        is_command = arg["command"]
        try:
            if is_command:
                self.command_reception_callback(arg["cmd"])
            else:
                self.notification_reception_callback(arg["notification"])
        except:
            logger.error("Error in message received format")
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
        self.connected = False
        self.lo.disconnect()

    def publish(
        self,
        topic: str,
        message: Msg,
    ) -> bool:
        """
        Try to publish a message to Live Objects
        """
        logger.info(f"Trying to publish message  {message} to topic {topic}")
        if not self.connected:
            logger.info(f"Not connected to LiveObjects, launching connection procedure")
            if not self.connect(self.max_connection_retries):
                return False
        try:
            self.lo.add_to_payload(topic, message)
            self.lo.send_data()
        except Exception as e:
            logger.error(f"Error when tryng to publish message to Live Objects")
            return False
        return True
