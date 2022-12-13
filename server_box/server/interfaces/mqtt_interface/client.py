import logging
from typing import Callable
import time
from socket import error as socket_error
from socket import timeout as socket_timeout
import paho.mqtt.client as mqtt
from .model import Msg, serialize, deserialize

logger = logging.getLogger(__name__)


class MQTTClient:
    """Service class for MQTT client"""

    def __init__(
        self,
        broker_address: str,
        username: str,
        password: str = None,
        subscriptions: dict = None,
        qos: int = 1,
        reconnection_timeout_in_secs: int = 5,
        publish_timeout_in_secs: int = 1,
    ):
        uid = str(time.time_ns())
        self.username = f"{username}_{uid}"
        self.broker_address = broker_address
        self.password = password
        self.subscriptions = subscriptions
        self.qos = qos
        self._callbacks = {}
        self.connected = False
        self.reconnection_timeout_in_secs = reconnection_timeout_in_secs
        self.publish_timeout_in_secs = publish_timeout_in_secs

        self._client = mqtt.Client(self.username)
        if password:
            self._client.username_pw_set(username=self.username, password=self.password)

        def on_connect(client, userdata, flags, rc, qos=1):
            """When cnnection is established"""

            logger.info("MQTT Client connection established")
            if self.subscriptions is not None:
                for topic, callback in self.subscriptions.items():
                    self.subscribe(topic, callback, qos)
                    logger.info(f"Subscribed to topic: {topic} qos: {qos}")
            self.connected = True

        def on_disconnect(client, userdata, reasonCode):
            """Stop reading and notify upon disconnecting"""

            logger.info("MQTT Client disconnected")
            self.connected = False
            self.loop_stop()

        def on_subscribe(client, userdata, mid, granted_qos):
            """Notify upon subscription"""

            logger.debug("Subscription done garanted_qos: " + str(granted_qos))

        def on_message(client, userdata, message):
            """Notify upon message reception"""

            logger.info(f"Message received on topic {message.topic}")
            logger.debug(f"   mid : {message.mid}")
            logger.debug(f"   duplicated : {message.dup}")
            logger.debug(f"   qos : {message.qos}")
            callback = self._callbacks[message.topic]
            if callback:
                try:
                    msg = deserialize(message.payload)
                    logger.info(f"Message : {str(msg)}")
                    callback(msg)
                except Exception:
                    logger.exception("Message processing failed")
                    raise

        def on_publish(client, userdata, mid):
            """Notify upon publishing message on queue"""

            logger.debug("Message puback received for message mid: %s", str(mid))

        self._client.on_connect = on_connect
        self._client.on_disconnect = on_disconnect
        self._client.on_subscribe = on_subscribe
        self._client.on_message = on_message
        self._client.on_publish = on_publish

    def connect(self):
        """Connect to broker, retry if connection unsuccessful"""

        try:
            self._client.connect(self.broker_address)
            time.sleep(1)
            return
        except (socket_error, socket_timeout):
            self.connected = False
            logger.exception("Connection to broker unsuccessful")
            logger.info("Retrying connection ...")
            time.sleep(self.reconnection_timeout_in_secs)
            return self.connect()

    def disconnect(self):
        """Send disconnection message to broker"""

        logger.info("Disconnect from broker")
        self._client.disconnect()

    def publish(self, topic: str, message: Msg, qos=1):
        """
        Try to publish a message to the broker, if errorin publish launch reconnection
        """

        logger.info(f"Publish message on topic {topic}")
        logger.info(f"Message : {str(message)}")
        message_publish_info = self._client.publish(topic, serialize(message), qos)
        logger.debug("trying to publish message mid: %s", str(message_publish_info.mid))
        try:
            message_publish_info.wait_for_publish(timeout=self.publish_timeout_in_secs)
        except:
            logger.exception(
                f"Error when tryng to publish message mid: {message_publish_info.mid} launching"
                " reconnection procedure"
            )
        if not message_publish_info._published:
            logger.exception(f"The message mid: {message_publish_info.mid} could not be published")
            logger.exception(f"Launching reconnection procedure")
            try:
                self.connect()
                self.loop_start()
            except socket_error:
                return self.publish(topic, message)
            return self.publish(topic, message)
        return message_publish_info

    def subscribe(self, topic: str, callback: Callable[[Msg], None], qos=1):
        """Subscribe to a topic"""

        logger.info(f"Subscribe to topic {topic}")
        self._callbacks[topic] = callback

        return self._client.subscribe(topic, qos)

    def loop_forever(self):
        """Run loop forever"""

        logger.info("Run infinite loop")
        self._client.loop_forever()

    def loop_start(self):
        """Run loop in dedicated thread"""

        logger.info("Start loop in dedicated thread")
        return self._client.loop_start()

    def loop_stop(self):
        """Stop running loop"""

        logger.info("Stop loop")
        return self._client.loop_stop()
