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


def load_ml_model():
    # print("Loading ML model...", flush=True)
    # Model 1
    ml_model_loaded = joblib.load(f"{PathConfig.MODEL_FOLDER}/{PathConfig.MODEL_1}")

    # print(ml_model_loaded, flush=True)

    return ml_model_loaded


def load_plsr_model():
    print("Loading PLSR model...", flush=True)
    # Model 2
    loaded_pls_model = joblib.load(f"{PathConfig.MODEL_FOLDER}/{PathConfig.MODEL_2}")

    print(loaded_pls_model, flush=True)

    return loaded_pls_model


def load_scaler(scaler_path):
    loaded_scaler = joblib.load(f"{PathConfig.MODEL_FOLDER}/{scaler_path}")

    return loaded_scaler


def prepare_ml_features(data):
    try:
        features = np.array([[data[col] for col in PostgresConfig.PILOT_COLUMNS]])
        return features
    except KeyError as e:
        print(f"❌ Missing data field: {e}")
        return None


def predict_ml_model(data, model):
    # print(data, flush=True)
    features = prepare_ml_features(data)[0].T
    scaler_X = joblib.load(f"{PathConfig.MODEL_FOLDER}/{PathConfig.MODEL_1_SCALER_X}")
    scaler_y = joblib.load(f"{PathConfig.MODEL_FOLDER}/{PathConfig.MODEL_1_SCALER_Y}")

    if features is not None:
        # print(features.shape, flush=True)
        # if feature is vector, reshape to 2D array
        if features.ndim == 1:
            features = features.reshape(1, -1)
        # print(features.shape, flush=True)
        features_scaled = scaler_X.transform(features)
        # print(features_scaled, flush=True)
        # print(features_scaled.shape, flush=True)

        prediction_scaled = model.predict(features_scaled)

        # print(prediction_scaled, flush=True)
        # print(prediction_scaled.shape, flush=True)

        prediction = scaler_y.inverse_transform(prediction_scaled.reshape(-1, 1))
        # print(prediction, flush=True)
        return prediction
    return None


def prepare_raman_features(data, scaler_x):
    # print("Preparing Raman features...", flush=True)
    try:
        # print(data, flush=True)
        df_features = pd.DataFrame(data, columns=PostgresConfig.FTIR_COLUMNS)
        # print("df_features", flush=True)
        scaled_features = scaler_x.transform(df_features)
        return scaled_features
    except KeyError as e:
        print(f"❌ Missing Raman field: {e}", flush=True)
        return None

def predict_raman(data, pls_model):
    # print("Predicting Raman data...", flush=True)
    # print(data, flush=True)
    scaler_x = load_scaler(PathConfig.MODEL_2_SCALER_X)
    scaler_y = load_scaler(PathConfig.MODEL_2_SCALER_Y)
    scaled_features = prepare_raman_features(data, scaler_x)
    # print(scaled_features, flush=True)

    if scaled_features is not None:
        prediction = pls_model.predict(scaled_features)
        prediction = scaler_y.inverse_transform(prediction)
        return prediction
    return None

