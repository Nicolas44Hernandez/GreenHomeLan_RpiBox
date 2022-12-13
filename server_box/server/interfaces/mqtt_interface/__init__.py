"""MQTT interface package"""

# TODO: this package must be a single library used by all the modules that use MQTT

from .client import MQTTClient as mqtt_client_interface
from .model import SingleRelayStatus, RelaysStatus
