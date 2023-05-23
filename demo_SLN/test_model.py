
#import joblib
# from sklearn.preprocessing import StandardScaler, RobustScaler
#import xgboost as xgb
import pickle
#import numpy
#import pandas
#import datetime

MODEL="/home/pi/workspace/GreenHomeLan_RpiBox/demo_SLN/model/XGBRegressor.sav"
SCALER ="/home/pi/workspace/GreenHomeLan_RpiBox/demo_SLN/scaler/scaler.gz"
DATA_TEST="/home/pi/workspace/GreenHomeLan_RpiBox/demo_SLN/data/X_test.csv"


# def load_test_data(csv_file: str):
#     """Load test CSV data"""
#     df = pandas.read_csv(csv_file)
#     #print(df)
#     return df

#start = datetime.datetime.now()
# Load Model
model = pickle.load(open(MODEL, 'rb'))

# # load scaler
# scaler = joblib.load(SCALER)
# end = datetime.datetime.now()
# model_load_time = end - start

# # load data test
# dataset = load_test_data(DATA_TEST)
# small_dataset = dataset.iloc[1:2]

# predictions = []
# inference_times = []

# # Loop over data
# for idx in range(len(dataset)):
#     start = datetime.datetime.now()
#     # Extract dataframe
#     df = dataset.iloc[idx:idx+1]
#     # Transform data
#     df_transformed = scaler.transform(df)
#     predictions.append(model.predict(df_transformed))
#     end = datetime.datetime.now()
#     inference_time = end - start
#     inference_times.append(inference_time.total_seconds())

# #numpy.savetxt("results.csv", predictions, delimiter=",")

# # Calculate mean inference time
# mean_inference_time = sum(inference_times) / len(inference_times)
# print("----------------------------------------------------------------")
# print(f"Model load time: {model_load_time}")
# print(f"Mean inference time: {mean_inference_time}")

