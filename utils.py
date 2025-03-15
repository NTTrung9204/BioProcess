from config import PostgresConfig, RouterConfig, PathConfig

import requests
import xgboost as xgb
import joblib
import numpy as np
import pandas as pd

def get_producer_status():
    try:
        response = requests.get(
            f"{RouterConfig.BASE_URL}/{RouterConfig.ROUTE_PRODUCER_STATUS}"
        )
        return response.json().get("producer_running", True)
    except:
        return True


def map_record(record):
    new_record = {}
    for key, value in record.items():
        new_key = PostgresConfig.COLUMN_MAPPING.get(key, key)
        new_record[new_key] = value
    return new_record


def load_xgboost_model():
    loaded_xgb_model = xgb.XGBRegressor()
    loaded_xgb_model.load_model(f"{PathConfig.MODEL_FOLDER}/{PathConfig.XGBOOST_MODEL}")

    return loaded_xgb_model


def load_plsr_model():
    loaded_pls_model = joblib.load(f"{PathConfig.MODEL_FOLDER}/{PathConfig.PLS_MODEL}")

    return loaded_pls_model


def load_scaler(scaler_path):
    loaded_scaler = joblib.load(f"{PathConfig.MODEL_FOLDER}/{scaler_path}")

    return loaded_scaler


def prepare_xgb_features(data):
    try:
        features = np.array([[data[col] for col in PostgresConfig.OPERATION_COLUMNS]])
        return features
    except KeyError as e:
        print(f"❌ Missing data field: {e}")
        return None


def predict_xgb(data, model):
    features = prepare_xgb_features(data)
    if features is not None:
        prediction = model.predict(features)[0]
        return float(prediction)
    return None


def prepare_raman_features(data, scaler_x):
    try:
        df_features = pd.DataFrame([data], columns=PostgresConfig.RAMAN_COLUMNS)
        scaled_features = scaler_x.transform(df_features)
        return scaled_features
    except KeyError as e:
        print(f"❌ Missing Raman field: {e}")
        return None


def predict_raman(data, pls_model, scaler_x, scaler_y):
    scaled_features = prepare_raman_features(data, scaler_x)
    if scaled_features is not None:
        prediction = pls_model.predict(scaled_features)
        prediction = scaler_y.inverse_transform(prediction)
        return float(prediction[0, 0])
    return None

