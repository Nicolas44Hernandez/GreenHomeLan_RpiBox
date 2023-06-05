"""Data model for 5GHz band on/off manager package"""
from dataclasses import dataclass
from typing import Iterable
from datetime import datetime

@dataclass
class Prediction:
    """Model for prediction"""
    station: str
    timestamp: datetime
    predicted_rtt: float

@dataclass
class BandCountersSample:
    """Model for bands  counters sampole"""
    tx_rate_2GHz_Mbps: float
    rx_rate_2GHz_Mbps: float
    tx_rate_5GHz_Mbps: float
    rx_rate_5GHz_Mbps: float

@dataclass
class StationCountersSample:
    """Model for Station counters sample"""
    txbytes: float
    rxbytes: float
    band: str
    timestamp: datetime

@dataclass
class StationThroughputSample:
    """Model for Station throughput sample"""
    tx_rate_Mbps: float
    rx_rate_Mbps: float

