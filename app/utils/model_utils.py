import joblib
import numpy as np
import pandas as pd
from app.config import PostgresConfig, PathConfig

def load_ml_model():
    """
    Load the XGBoost machine learning model
    """
    ml_model_loaded = joblib.load(f"app/{PathConfig.MODEL_FOLDER}/{PathConfig.MODEL_1}")
    return ml_model_loaded

def load_plsr_model():
    """
    Load the PLS regression model
    """
    print("Loading PLSR model...", flush=True)
    loaded_pls_model = joblib.load(f"app/{PathConfig.MODEL_FOLDER}/{PathConfig.MODEL_2}")
    print(loaded_pls_model, flush=True)
    return loaded_pls_model

def load_scaler(scaler_path):
    """
    Load a scaler model from the given path
    """
    loaded_scaler = joblib.load(f"app/{PathConfig.MODEL_FOLDER}/{scaler_path}")
    return loaded_scaler

def prepare_ml_features(data):
    """
    Extract and prepare features for the machine learning model
    """
    try:
        features = np.array([[data[col] for col in PostgresConfig.PILOT_COLUMNS]])
        return features
    except KeyError as e:
        print(f"❌ Missing data field: {e}")
        return None

def predict_ml_model(data, model):
    """
    Make predictions using the ML model with proper scaling
    """
    features = prepare_ml_features(data)[0].T
    scaler_X = joblib.load(f"app/{PathConfig.MODEL_FOLDER}/{PathConfig.MODEL_1_SCALER_X}")
    scaler_y = joblib.load(f"app/{PathConfig.MODEL_FOLDER}/{PathConfig.MODEL_1_SCALER_Y}")

    if features is not None:
        if features.ndim == 1:
            features = features.reshape(1, -1)
        features_scaled = scaler_X.transform(features)
        prediction_scaled = model.predict(features_scaled)
        prediction = scaler_y.inverse_transform(prediction_scaled.reshape(-1, 1))
        return prediction
    return None

def prepare_raman_features(data, scaler_x):
    """
    Extract and prepare features for the Raman model
    """
    print("Preparing Raman features...", flush=True)
    try:
        print(data, flush=True)
        print(PostgresConfig.FTIR_COLUMNS, flush=True)
        df_features = pd.DataFrame(data, columns=PostgresConfig.FTIR_COLUMNS)
        print("df_features", flush=True)
        print(df_features, flush=True)
        scaled_features = scaler_x.transform(df_features)
        return scaled_features
    except KeyError as e:
        print(f"❌ Missing Raman field: {e}", flush=True)
        return None

def predict_raman(data, pls_model):
    """
    Make predictions using the Raman model with proper scaling
    """
    print("Predicting Raman data...", flush=True)
    scaler_x = load_scaler(PathConfig.MODEL_2_SCALER_X)
    scaler_y = load_scaler(PathConfig.MODEL_2_SCALER_Y)
    scaled_features = prepare_raman_features(data, scaler_x)
    print("1111", scaled_features, flush=True)

    if scaled_features is not None:
        prediction = pls_model.predict(scaled_features)
        print("2222", prediction, flush=True)
        prediction = scaler_y.inverse_transform(prediction)
        return prediction
    return None 