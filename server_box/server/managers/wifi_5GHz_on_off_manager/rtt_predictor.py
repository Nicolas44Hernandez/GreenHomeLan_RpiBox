"""
RTT Predictor service
"""

import joblib
import pickle
import pandas
import numpy as np
import logging
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)

class RttPredictor:
    """Service class for RTT Prediction by using a ML model"""
    model: str # TODO: add model type
    scaler: str # TODO: add scaler type
    min_predicted_rtt: float

    def __init__(self, model_path: str, scaler_path: str, min_predicted_rtt: float):
        self.scaler = self.load_scaler(scaler_path=scaler_path)
        self.model = self.load_model(model_path=model_path)
        self.min_predicted_rtt=[min_predicted_rtt]

    def load_scaler(self, scaler_path: str):
        """Load scaler for data transformation"""
        logger.info(f"Loading scaler: {scaler_path}")
        try:
            return joblib.load(scaler_path)
        except:
            logger.error("Error in scaler load")
            raise ServerBoxException(ErrorCode.ERROR_IN_PREDICTOR_MODEL_LOAD)

    def load_model(self, model_path: str):
        """Load model to RTT prediction inferences"""
        logger.info(f"Loading model: {model_path}")
        try:
            return pickle.load(open(model_path, 'rb'))
        except:
            logger.error("Error in model load")
            raise ServerBoxException(ErrorCode.ERROR_IN_PREDICTOR_MODEL_LOAD)

    def predict_rtt(self, tx_Mbps_2g: float, rx_Mbps_2g: float, tx_Mbps: float, rx_Mbps: float):
        """Predict rtt for values in args"""
        #logger.info(f"Performing inference over tx_Mbps_2g:{tx_Mbps_2g}  rx_Mbps_2g{rx_Mbps_2g}  tx_Mbps:{tx_Mbps}  rx_Mbps:{rx_Mbps}")
        # Create dataframe from data in args
        data= np.array([[tx_Mbps_2g, rx_Mbps_2g, tx_Mbps, rx_Mbps]])
        dataframe = pandas.DataFrame(data=data)

        # Transform dataframe using scaler
        dataframe_transformed = self.scaler.transform(dataframe)

        # Perform inference
        predicted_rtt = self.model.predict(dataframe_transformed)
        if predicted_rtt < self.min_predicted_rtt:
            predicted_rtt=self.min_predicted_rtt
        #logger.info(f"Predicted RTT: {predicted_rtt}")
        return float(predicted_rtt[0])

