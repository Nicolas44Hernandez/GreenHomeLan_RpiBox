"""Wifi 5GHz band on/off managment package"""

import logging
import requests
from requests.exceptions import ConnectionError, InvalidURL
from flask import Flask
from datetime import datetime
from statistics import mean
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from .rtt_predictor import RttPredictor
from .model import BandCountersSample, StationCountersSample, StationThroughputSample

logger = logging.getLogger(__name__)

class Wifi5GHzOnOffManager:
    """Manager for 5GHz on/off control"""
    rtt_predictions: dict
    wifi_5GHz_band_status: bool
    last_txbytes: float
    last_rxbytes: float
    last_sample_timestamp: datetime
    last_stations_samples: dict
    predictor: RttPredictor
    instant_rtt_predictions_list_max_size: int
    avg_rtt_predictions_list_max_size: int
    rtt_th_for_5GHz_on: float
    service_active: bool
    rtt_predictions_cloud_ip: str
    rtt_predictions_cloud_port: int
    rtt_predictions_cloud_path: str
    rtt_predictions_service_status_cloud_path: str
    st1_for_cloud_notification_mac: str
    st2_for_cloud_notification_mac: str

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize Wifi5GHzOnOffManager"""
        if app is not None:
            logger.info("initializing the Wifi5GHzOnOffManager")
            # Initialize configuration
            self.wifi_5GHz_band_status=wifi_bands_manager_service.get_band_status(band="5GHz")
            self.last_sample_timestamp = None
            self.last_stations_samples = {}
            self.rtt_predictions = {}
            self.last_txbytes_2GHz= None
            self.last_rxbytes_2GHz= None
            self.last_txbytes_5GHz= None
            self.last_rxbytes_5GHz= None
            self.predictor=RttPredictor(
                model_path=app.config["RTT_PREDICTOR_MODEL"],
                scaler_path=app.config["RTT_PREDICTOR_SCALER"],
                min_predicted_rtt=app.config["MIN_PREDICTED_RTT_IN_MS"],
            )
            self.instant_rtt_predictions_list_max_size = app.config["RTT_INSTANT_PREDICTIONS_LIST_MAX_SIZE"]
            self.avg_rtt_predictions_list_max_size = app.config["RTT_AVG_PREDICTIONS_LIST_MAX_SIZE"]
            self.rtt_th_for_5GHz_on=app.config["PREDICTED_RTT_TH_5GHZ_ON"]
            self.service_active=app.config["ON_OFF_5GHZ_SERVICE_ACTIVE"]
            self.rtt_predictions_cloud_ip=app.config["RTT_PREDICTIONS_CLOUD_IP"]
            self.rtt_predictions_cloud_port=app.config["RTT_PREDICTIONS_CLOUD_PORT"]
            self.rtt_predictions_cloud_path=app.config["RTT_PREDICTIONS_CLOUD_PATH"]
            self.rtt_predictions_service_status_cloud_path=app.config["RTT_PREDICTIONS_SERVICE_STATUS_PATH"]
            self.st1_for_cloud_notification_mac=app.config["ST1_IN_CLOUD_MAC"]
            self.st2_for_cloud_notification_mac=app.config["ST2_IN_CLOUD_MAC"]


    def perform_prediction(self):
        """Get bands and stations counters and perform RTT predictions"""

        # Notify service status
        self.notify_service_status_to_cloud_server()

        if not self.service_active:
            logger.info(f"5GHz ON/OFF service is inactive")
            return

        # Flag for prediction
        perform_prediction = True

        # Update 5GHz band status
        self.wifi_5GHz_band_status=wifi_bands_manager_service.get_band_status(band="5GHz")

        # Get bands throughputs sample
        bands_counters_sample = self.get_sample_bands_counters()
        if bands_counters_sample is None:
            logger.info("Prediction not performed")
            return

        # Get connected stations counters sample
        connected_stations_counters_sample = self.get_sample_connected_stations_counters()

        # Filter throughputs lower than 0.02 Mbps and higher than 20 Mbps
        total_tx_throughput_Mbps = bands_counters_sample.tx_rate_2GHz_Mbps + bands_counters_sample.tx_rate_5GHz_Mbps
        total_rx_throughput_Mbps = bands_counters_sample.rx_rate_2GHz_Mbps + bands_counters_sample.rx_rate_5GHz_Mbps
        total_throughput =  total_tx_throughput_Mbps + total_rx_throughput_Mbps
        total_2GHz_throughput=bands_counters_sample.tx_rate_2GHz_Mbps + bands_counters_sample.rx_rate_2GHz_Mbps
        total_5GHz_throughput=bands_counters_sample.tx_rate_5GHz_Mbps + bands_counters_sample.rx_rate_5GHz_Mbps
        low_rtt = False

        if total_throughput < 0.02:
            if not self.wifi_5GHz_band_status:
                logger.info("Prediction not performed, total throughput is too low")
                perform_prediction = False
            else:
                low_rtt=True

        if total_throughput > 40:
            perform_prediction = False
            logger.info("Prediction not performed, total throughput is too high")

        # To notify cloud
        iteration_predictions = {}
        for station in connected_stations_counters_sample:
            iteration_predictions[station]=10

        # Perform predictions
        for station in connected_stations_counters_sample:
            try:
                prediction_timestamp = datetime.now()
                station_total_traffic = connected_stations_counters_sample[station].rx_rate_Mbps + connected_stations_counters_sample[station].tx_rate_Mbps
                # For low troughtputs assume low RTT
                if low_rtt or not perform_prediction:
                    predicted_rtt = 10

                # if not low throughput in box but low traffic in station assume low RTT
                elif station_total_traffic < 0.02:
                    predicted_rtt = 10

                else:
                    predicted_rtt = self.predictor.predict_rtt(
                        tx_Mbps_2g=total_tx_throughput_Mbps,
                        rx_Mbps_2g=total_rx_throughput_Mbps,
                        tx_Mbps=connected_stations_counters_sample[station].tx_rate_Mbps,
                        rx_Mbps=connected_stations_counters_sample[station].rx_rate_Mbps,
                    )

                iteration_predictions[station]=predicted_rtt
                #logger.info(f"For station {station} instant predicted_RTT={predicted_rtt}")

                # Add prediction to station RTT list
                self.add_prediction_to_station_rtt_list(
                    station=station,
                    predicted_rtt=predicted_rtt,
                    prediction_timestamp=prediction_timestamp
                )
                logger.info(f"rtt_predictions: {self.rtt_predictions}")

                # Evaluate if is necessary to ON/OFF the 5GHz band
                self.evaluate_5GHz_band_on_off()

            except Exception as e:
                logger.error("Error in prediction")

        self.notify_rtt_prediction_to_cloud_server(
            livebox_traffic=total_throughput,
            band_5GHz_traffic=total_5GHz_throughput,
            band_2GHz_traffic=total_2GHz_throughput,
            stations_counters=connected_stations_counters_sample,
            rtt_predictions=iteration_predictions
        )

    def evaluate_5GHz_band_on_off(self):
        """Evaluate if its necessary to turn on/off  5GHz band"""

        new_band_status = None
        for station in self.rtt_predictions:
            #If the avg rtt predictions list for station is full
            if len(self.rtt_predictions[station]["avg_rtt_predictions"]) == self.avg_rtt_predictions_list_max_size:
                # Get max value
                max_rtt = max(self.rtt_predictions[station]["avg_rtt_predictions"])

                # If max average rtt for at least one station is higher than threshold turn on 5GHz band
                if max_rtt >= self.rtt_th_for_5GHz_on:
                    new_band_status=True
                    break
                else:
                    new_band_status=False

        if new_band_status is not None:
            if self.wifi_5GHz_band_status != new_band_status:
                status = "ON" if new_band_status else "OFF"
                logger.info(f"Setting 5GHz BAND {status}")
                wifi_bands_manager_service.set_band_status(band="5GHz", status=new_band_status)
                self.wifi_5GHz_band_status=new_band_status


    def add_prediction_to_station_rtt_list(self, station:str, predicted_rtt: float, prediction_timestamp: datetime):
        """Add predicted rtt to station rtt list"""
        # Remove stations that have disconnected a while ago
        stations_to_delete = []
        for candidate_station in self.rtt_predictions:
            # if sample timestamp is too old clear from dictionary
            _delta = datetime.now() - self.rtt_predictions[candidate_station]["last_prediction_timestamp"]
            delta_time_in_secs = _delta.seconds + (_delta.microseconds / 1000000.0)
            if delta_time_in_secs > 30:
                stations_to_delete.append(candidate_station)
                continue

        # Clean dictionary
        for station_to_delete in stations_to_delete:
            del self.rtt_predictions[station_to_delete]

        # Add station to dictionary if not present
        if station not in self.rtt_predictions:
            _dict_entry = {
                "instant_rtt_predictions": [predicted_rtt],
                "avg_rtt_predictions": [],
                "last_prediction_timestamp": prediction_timestamp
            }
            self.rtt_predictions[station] = _dict_entry

        else:
            # if last prediction timestamp is too old, clear list
            _delta = prediction_timestamp - self.rtt_predictions[station]["last_prediction_timestamp"]
            _delta_time_in_secs = _delta.seconds + (_delta.microseconds / 1000000.0)

            if _delta_time_in_secs > 40:
                self.rtt_predictions[station]["instant_rtt_predictions"] = []

            # If instant rtt predictions list is max len pop oldest prediction
            if len(self.rtt_predictions[station]["instant_rtt_predictions"]) == self.instant_rtt_predictions_list_max_size:
                self.rtt_predictions[station]["instant_rtt_predictions"].pop(0)

            # Add prediction to list
            self.rtt_predictions[station]["instant_rtt_predictions"].append(predicted_rtt)
            self.rtt_predictions[station]["last_prediction_timestamp"] = prediction_timestamp

            # If avg rtt predictions list is max len pop oldest avg prediction
            if len(self.rtt_predictions[station]["avg_rtt_predictions"]) == self.avg_rtt_predictions_list_max_size:
                self.rtt_predictions[station]["avg_rtt_predictions"].pop(0)

            # If instant rtt predictions list is max len calculate avg rtt and append to list
            if len(self.rtt_predictions[station]["instant_rtt_predictions"]) == self.instant_rtt_predictions_list_max_size:
                avg_rtt = mean(self.rtt_predictions[station]["instant_rtt_predictions"])
                self.rtt_predictions[station]["avg_rtt_predictions"].append(avg_rtt)


    def get_sample_connected_stations_counters(self):
        """Take connected stations tx and rx counters samples"""
        connected_stations_sample = {}
        current_sample_timestamp=datetime.now()

        # Get connected stations and band
        connected_stations = {}
        total_connections, connected_stations_2_4GHz, connected_stations_5GHz = wifi_bands_manager_service.get_connected_stations_by_band_mac_list()
        for station in connected_stations_2_4GHz:
            connected_stations[station]="2.4GHz"
        for station in connected_stations_5GHz:
            connected_stations[station]="5GHz"

        #Loop over connected stations to clean non connected stations and too old timestamps
        stations_to_clean = []
        for station in self.last_stations_samples:
            # if station not connected clean from dictionay
            if station not in connected_stations:
                stations_to_clean.append(station)
                continue
            # if sample timestamp is too old clear from dictionary
            _delta = current_sample_timestamp - self.last_stations_samples[station].timestamp
            delta_time_in_secs = _delta.seconds + (_delta.microseconds / 1000000.0)
            if delta_time_in_secs > 40:
                stations_to_clean.append(station)
                continue

        # Clean dictionary
        for station in stations_to_clean:
            del self.last_stations_samples[station]

        # Loop over connected stations to get samples
        for station in connected_stations:
            # Get connected stations counters
            current_sample_timestamp=datetime.now()
            _band=connected_stations[station]
            station_txbytes, station_rxbytes = self.get_station_tx_rx_counters(station_mac=station, band=_band)

            # If its the first sample or values are set to None
            if station not in self.last_stations_samples or self.last_stations_samples[station].band != _band :
                self.last_stations_samples[station] = StationCountersSample(
                    txbytes=station_txbytes,
                    rxbytes=station_rxbytes,
                    band=_band,
                    timestamp=current_sample_timestamp
                )
                logger.info(f"First txbytes and rxbytes sample setted for station {station}")
                continue

            # Compute rx and tx bytes since last sample
            txbytes_sample = station_txbytes - self.last_stations_samples[station].txbytes
            rxbytes_sample = station_rxbytes - self.last_stations_samples[station].rxbytes

            # Compute station throughputs
            station_tx_rate_Mbps = (txbytes_sample * (8 / 1000000)) / delta_time_in_secs
            station_rx_rate_Mbps = (rxbytes_sample * (8 / 1000000)) / delta_time_in_secs

            # Update station counters with new values from sample
            self.last_stations_samples[station] = StationCountersSample(
                    txbytes=station_txbytes,
                    rxbytes=station_rxbytes,
                    band=_band,
                    timestamp=current_sample_timestamp
                )

            # Fix for negative datates (32 bits cyclic counter)
            if station_tx_rate_Mbps < 0 or station_rx_rate_Mbps < 0:
                logger.error("Error in sample, data discarted")
                continue

            # Set station throughputs in result dict
            connected_stations_sample[station] = StationThroughputSample(
                tx_rate_Mbps=station_tx_rate_Mbps,
                rx_rate_Mbps=station_rx_rate_Mbps
            )

            # Log station counters
            # logger.info(f"{station}  tx_rate_Mbps: {connected_stations_sample[station].tx_rate_Mbps} rx_rate_Mbps: {connected_stations_sample[station].rx_rate_Mbps}")
            logger.info(
                "station %s tx_rate_Mbps:%.3f  rx_rate_Mbps:%.3f",
                station,
                connected_stations_sample[station].tx_rate_Mbps,
                connected_stations_sample[station].rx_rate_Mbps,
            )

        return connected_stations_sample

    def get_sample_bands_counters(self):
        """Take bands tx and rx counters samples and update last values"""

        # Get bands counters
        txbytes_2GHz, rxbytes_2GHz = self.get_band_tx_rx_counters(band="2.4GHz")
        txbytes_5GHz, rxbytes_5GHz = self.get_band_tx_rx_counters(band="5GHz")

        # Get current timestamp
        current_prediction_timestamp = datetime.now()

        # If its the first sample or values are set to None
        if self.last_sample_timestamp is None:
            self.last_sample_timestamp = current_prediction_timestamp
            self.last_txbytes_2GHz= txbytes_2GHz
            self.last_rxbytes_2GHz= rxbytes_2GHz
            self.last_txbytes_5GHz= txbytes_5GHz
            self.last_rxbytes_5GHz= rxbytes_5GHz
            logger.info("First txbytes and rxbytes sample setted")
            return None

        # Calculate deltatime with last sample
        _delta = current_prediction_timestamp - self.last_sample_timestamp
        delta_time_in_secs = _delta.seconds + (_delta.microseconds / 1000000.0)

        # If delta is too old restart counters
        if delta_time_in_secs > 40:
            logger.info("Last sample taken is too old, restarting counters")
            self.last_sample_timestamp = current_prediction_timestamp
            self.last_txbytes_2GHz= txbytes_2GHz
            self.last_rxbytes_2GHz= rxbytes_2GHz
            self.last_txbytes_5GHz= txbytes_5GHz
            self.last_rxbytes_5GHz= rxbytes_5GHz
            return None

        # Log txbytes rxbytes
        #logger.info(f"txbytes_2GHz:{txbytes_2GHz} rxbytes_2GHz:{rxbytes_2GHz}   txbytes_5GHz:{txbytes_5GHz} rxbytes_5GHz:{rxbytes_5GHz}")

        # Compute rx and tx bytes since last sample
        txbytes_sample_2GHz = txbytes_2GHz - self.last_txbytes_2GHz
        rxbytes_sample_2GHz = rxbytes_2GHz - self.last_rxbytes_2GHz
        txbytes_sample_5GHz = txbytes_5GHz - self.last_txbytes_5GHz
        rxbytes_sample_5GHz = rxbytes_5GHz - self.last_rxbytes_5GHz

        # Fix for negative (32 bits cyclic counter)
        if txbytes_sample_2GHz < 0:
            txbytes_sample_2GHz = txbytes_2GHz + (2**32 - self.last_txbytes_2GHz)
        if rxbytes_sample_2GHz < 0:
            rxbytes_sample_2GHz = rxbytes_2GHz + (2**32 - self.last_rxbytes_2GHz)
        if txbytes_sample_5GHz < 0:
            txbytes_sample_5GHz = txbytes_5GHz + (2**32 - self.last_txbytes_5GHz)
        if rxbytes_sample_5GHz < 0:
            rxbytes_sample_5GHz = rxbytes_5GHz + (2**32 - self.last_rxbytes_5GHz)

        # Compute throughput in Mbps
        tx_rate_2GHz_Mbps = (txbytes_sample_2GHz * (8 / 1000000)) / delta_time_in_secs
        rx_rate_2GHz_Mbps = (rxbytes_sample_2GHz * (8 / 1000000)) / delta_time_in_secs
        tx_rate_5GHz_Mbps = (txbytes_sample_5GHz * (8 / 1000000)) / delta_time_in_secs
        rx_rate_5GHz_Mbps = (rxbytes_sample_5GHz * (8 / 1000000)) / delta_time_in_secs

        # Log throughput
        logger.info(
            "Livebox tx_rate_2GHz_Mbps:%.3f  rx_rate_2GHz_Mbps:%.3f   tx_rate_5GHz_Mbps:%.3f  rx_rate_5GHz_Mbps:%.3f",
            tx_rate_2GHz_Mbps,
            rx_rate_2GHz_Mbps,
            tx_rate_5GHz_Mbps,
            rx_rate_5GHz_Mbps
        )

        # Update last sample taken value
        self.last_sample_timestamp = current_prediction_timestamp
        self.last_txbytes_2GHz=txbytes_2GHz
        self.last_rxbytes_2GHz=rxbytes_2GHz
        self.last_txbytes_5GHz=txbytes_5GHz
        self.last_rxbytes_5GHz=rxbytes_5GHz

        # Return throughput values
        return BandCountersSample(
            tx_rate_2GHz_Mbps=tx_rate_2GHz_Mbps,
            rx_rate_2GHz_Mbps=rx_rate_2GHz_Mbps,
            tx_rate_5GHz_Mbps=tx_rate_5GHz_Mbps,
            rx_rate_5GHz_Mbps=rx_rate_5GHz_Mbps,
        )

    def get_band_tx_rx_counters(self, band:str):
        """Retrieve 5GHz tx and rx counters"""
        try:
            # Get tx and rx values
            commands_response = wifi_bands_manager_service.execute_telnet_commands(["WIFI", "counters", band])
            txbyte = int(commands_response.split("txbyte")[1].split(" ")[1])
            rxbyte = int(commands_response.split("rxbyte")[1].split(" ")[1])
            return txbyte, rxbyte
        except Exception:
            logger.error("Error in counters command execution")
            return None, None

    def get_station_tx_rx_counters(self, station_mac: str, band: str):
        """Get the station rx and rx counters"""

        if station_mac not in wifi_bands_manager_service.get_connected_stations_mac_list():
            logger.error(f"Station {station_mac} not connected")
            return None

        commands_response = wifi_bands_manager_service.execute_telnet_commands(["WIFI", "counters", "station_info", band], station_mac=station_mac)
        try:
            txbyte = int(commands_response.split("tx total bytes")[1].split(" ")[1])
            rxbyte = int(commands_response.split("rx data bytes")[1].split(" ")[1])
        except:
            logger.error("Error retreiving counters tx and rx throughput assumed to 0 Mbps ")
            return 0,0
        return txbyte, rxbyte

    def clear_predictions_counter(self):
        """Clear rtt prediction for all stations"""
        self.rtt_predictions = {}

    def set_service_status(self, status:bool):
        """Set service status active/inactive"""
        self.service_active=status

    def get_service_status(self):
        """Get service status"""
        return self.service_active

    def notify_rtt_prediction_to_cloud_server(
            self,
            livebox_traffic: float,
            band_5GHz_traffic: float,
            band_2GHz_traffic: float,
            stations_counters: dict,
            rtt_predictions: dict
        ):
        """Notify rtt predictions to cloud"""
        logger.info(f"Posting HTTP to notify rtt predictions to RPI cloud")

        # Get st1 and st2 traffic
        st1_traffic = 0
        st2_traffic = 0
        if self.st1_for_cloud_notification_mac in stations_counters:
            st1_traffic=stations_counters[self.st1_for_cloud_notification_mac].rx_rate_Mbps + stations_counters[self.st1_for_cloud_notification_mac].tx_rate_Mbps
        if self.st2_for_cloud_notification_mac in stations_counters:
            st2_traffic=stations_counters[self.st2_for_cloud_notification_mac].rx_rate_Mbps + stations_counters[self.st2_for_cloud_notification_mac].tx_rate_Mbps

        # Get st1 and st2 rtt predicted
        st1_rtt = None
        st2_rtt = None
        if self.st1_for_cloud_notification_mac in rtt_predictions:
            st1_rtt=rtt_predictions[self.st1_for_cloud_notification_mac]
        if self.st2_for_cloud_notification_mac in rtt_predictions:
            st2_rtt=rtt_predictions[self.st2_for_cloud_notification_mac]


        # Get band status
        band_status = 1 if self.wifi_5GHz_band_status else 0

        # Get mean rtt for st1 and st2
        st1_mean_rtt = None
        st2_mean_rtt = None
        if self.st1_for_cloud_notification_mac in self.rtt_predictions:
            if len(self.rtt_predictions[self.st1_for_cloud_notification_mac]["instant_rtt_predictions"]) == self.instant_rtt_predictions_list_max_size:
                st1_mean_rtt = mean(self.rtt_predictions[self.st1_for_cloud_notification_mac]["instant_rtt_predictions"])
        if self.st2_for_cloud_notification_mac in self.rtt_predictions:
            if len(self.rtt_predictions[self.st2_for_cloud_notification_mac]["instant_rtt_predictions"]) == self.instant_rtt_predictions_list_max_size:
                st2_mean_rtt = mean(self.rtt_predictions[self.st2_for_cloud_notification_mac]["instant_rtt_predictions"])

        # Prepare data to send
        data_to_send = {
            "livebox_traffic": livebox_traffic,
            "traffic_5GHz": band_5GHz_traffic,
            "traffic_2GHz": band_2GHz_traffic,
            "livebox_traffic": livebox_traffic,
            "st1_traffic": st1_traffic,
            "st2_traffic": st2_traffic,
            "st1_rtt": st1_rtt,
            "st2_rtt": st2_rtt,
            "st1_mean_rtt": st1_mean_rtt,
            "st2_mean_rtt": st2_mean_rtt,
            "band_5ghz_status": band_status,
        }
        # Post rtt predictions to rpi cloud
        post_url = (
                f"http://{self.rtt_predictions_cloud_ip}:{self.rtt_predictions_cloud_port}/{self.rtt_predictions_cloud_path}"
            )
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            rpi_cloud_response = requests.post(
                post_url, data=(data_to_send), headers=headers
            )
        except (ConnectionError, InvalidURL):
            logger.error(
                f"Error when posting rtt notification to rpi cloud, check if rpi cloud"
                f" server is running"
            )


    def notify_service_status_to_cloud_server(self):
        """Notify automatic 5GHz ON/OFF service status"""

        logger.info(f"notify service status {self.service_active} to cloud service ")
        # Prepare data to send
        data_to_send = {"status": self.service_active}
        # Post rtt predictions to rpi cloud
        post_url = (
                f"http://{self.rtt_predictions_cloud_ip}:{self.rtt_predictions_cloud_port}/{self.rtt_predictions_service_status_cloud_path}"
            )
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            rpi_cloud_response = requests.post(
                post_url, data=(data_to_send), headers=headers
            )
        except (ConnectionError, InvalidURL):
            logger.error(
                f"Error when posting rtt notification to rpi cloud, check if rpi cloud"
                f" server is running"
            )

wifi_5GHz_on_off_manager_service: Wifi5GHzOnOffManager = Wifi5GHzOnOffManager()
""" Wifi 5GHz on/off manager service singleton"""
