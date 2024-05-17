"""
MQTT messages model
"""

from typing import TypeVar 
import json

Msg = TypeVar("Msg")


def serialize(msg: Msg) -> bytes:
    """serialize MQTT message"""
    if type(msg) is dict:
        data_to_send = msg
    elif type(msg) is str:
        data_to_send = {"data":msg}
    else:
        data_to_send = msg.to_json()
    return json.dumps(data_to_send)


def deserialize(payload: bytes) -> Msg:
    """deserialize MQTT message"""
    data = json.loads(payload)
    return data
