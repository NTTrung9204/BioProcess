import base64
from datetime import datetime
from functools import wraps
import gc
import hashlib
import io
import itertools
import json
import os
import time
from flask import redirect, request, session, url_for
from kafka import KafkaConsumer, KafkaProducer
from matplotlib import pyplot as plt
import numpy as np
import optuna
import pandas as pd
import requests
from config import KafkaConfig, PathConfig, PostgresConfig, RunningConfig, UserConfig, HostConfig, KeyConfig, RouterConfig
from constants import Constants
from repositories import fetch_data, fetch_data_by_batch_id, fetch_new_data_by_batch_id, fetch_raman_data, insert_bulk_to_db, insert_data_to_db, query_database
from utils import (
    get_producer_status,
    load_plsr_model,
    load_scaler,
    load_ml_model,
    map_record,
    predict_raman,
    predict_ml_model,
)

def executive_query(custom_query):
    return query_database(custom_query)

def produce_data():
    print(f"✅ {KafkaConfig.KAFKA_BROKER}", flush=True)
    producer = KafkaProducer(
        bootstrap_servers=KafkaConfig.KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    print(f"✅ Producer running successfully", flush=True)

    scan = 0
    while True:
        records = fetch_data()
        if not records:
            print("No data in the database!")
            time.sleep(5)
            continue

        for record in records:
            if not get_producer_status():
                print("Producer paused...", flush=True)
                time.sleep(5)
                continue

            mapped_record = map_record(record)
            mapped_record[PostgresConfig.TIMESTAMP] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            mapped_record[PostgresConfig.SCAN] = scan

            producer.send(KafkaConfig.KAFKA_TOPIC_PILOT, value=mapped_record)

            print(
                f"Produced Operation: {record['timestamp']} | Scan: {scan}", flush=True
            )

            scan += 1
            time.sleep(2)

def stream_data_to_another_VM(data):
    KAFKA_TOPIC = KafkaConfig.KAFKA_TOPIC_PILOT
    KAFKA_REST_URL = f"http://{HostConfig.HOST_TARGET}/kafka-rest" # VM cua Vietnix

    headers = {
        'Content-Type': 'application/vnd.kafka.json.v2+json'
    }

    payload = {
        "records": [
            {
                "value": data
            }
        ]
    }

    response = requests.post(
        f"{KAFKA_REST_URL}/topics/{KAFKA_TOPIC}",
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code == 200:
        print(f"Produced Operation: {data['timestamp']}")
    else:
        print(f"Error producing message: {response.text}")

def consume_kafka():
    print("Kafka consumer starting...", flush=True)
    try:
        time.sleep(10)
        print("Initializing Kafka consumer...", flush=True)
        consumer = KafkaConsumer(
            *KafkaConfig.TOPICS,
            bootstrap_servers=KafkaConfig.KAFKA_BROKER,
            auto_offset_reset="earliest",
            group_id="sensor_group",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        print("✅ Kafka consumer successfully started...", flush=True)

        ml_model = load_ml_model()
        plsr_model = load_plsr_model()

        # print(ml_model, flush=True)
        # print(plsr_model, flush=True)
        # print(PostgresConfig.PILOT_COLUMNS, flush=True)

        scaler_x = load_scaler(PathConfig.MODEL_2_SCALER_X)
        scaler_y = load_scaler(PathConfig.MODEL_2_SCALER_Y)
        # print(KafkaConfig.TOPICS, flush=True)

        for message in consumer:
            data = message.value

            # print(data)
            # print(UserConfig.ADMIN_USERNAME, UserConfig.ADMIN_PASSWORD, flush=True)
            # print(UserConfig.ADMIN_USERNAME not in data)
            # print(data[UserConfig.ADMIN_USERNAME] != UserConfig.ADMIN_PASSWORD)

            if UserConfig.ADMIN_USERNAME not in data or data[UserConfig.ADMIN_USERNAME] != UserConfig.ADMIN_PASSWORD:
                print("Insufficient permissions to stream data!", flush=True)
                continue
            # else:
            #     print("TESTING", flush=True)

            if HostConfig.HOST_TARGET:    
                stream_data_to_another_VM(data)

            del data[UserConfig.ADMIN_USERNAME]

            if PostgresConfig.SCAN not in data or data[PostgresConfig.SCAN] is None:
                data[PostgresConfig.SCAN] = "empty_scan"

            if message.topic == KafkaConfig.KAFKA_TOPIC_PILOT:

                data[PostgresConfig.PREDICTED_OIL] = predict_ml_model(data, ml_model)[0][0]

                insert_data_to_db(
                    PostgresConfig.TABLE_NAME_PILOT, data, ml_model
                )
            elif message.topic == KafkaConfig.KAFKA_TOPIC_FTIR:
                # convert to df
                df = pd.DataFrame(data, index=[0])
                print(df.shape, flush=True)
                data[PostgresConfig.PREDICTED_OIL_CONCENTRATION] = predict_raman(df, plsr_model)[0][0]

                insert_data_to_db(
                    PostgresConfig.TABLE_NAME_FTIR,
                    data,
                    plsr_model,
                    scaler_x,
                    scaler_y,
                )

            print(
                f"📥 Received {data[PostgresConfig.TIMESTAMP]} from {message.topic}",
                flush=True,
            )

    except Exception as e:
        print(f"❌ Kafka consumer error: {e}")


def generate_doe_trials(param_ranges, num_intervals=4):
    param_values = {
        key: np.linspace(v[0], v[1], num_intervals) for key, v in param_ranges.items()
    }
    return [
        dict(zip(param_values.keys(), values))
        for values in itertools.product(*param_values.values())
    ]


def optimize_ml_model(
    optim_param_ranges, fixed_params, columns, socketio, n_trials, doe_intervals=4
):
    model = load_ml_model()

    def objective(trial):
        # features = []
        features = {}
        for col in columns:
            if col in optim_param_ranges:
                low, high = optim_param_ranges[col]
                value = trial.suggest_float(col, low, high)
            else:
                value = fixed_params[col]
            # features.append(value)
            features[col] = value
        # features_array = np.array([features])
        features_array = pd.DataFrame([features], columns=columns)
        # pred = model.predict(features_array)
        pred = predict_ml_model(features_array, model)
        return pred[0]

    def realtime_callback(study, trial):
        if trial.value is not None:
            socketio.emit(
                "trial_update",
                {"trial": trial.number, "params": trial.params, "value": trial.value},
            )

    study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(n_startup_trials=10)
    )

    doe_trials = generate_doe_trials(optim_param_ranges, num_intervals=doe_intervals)
    for trial_params in doe_trials:
        study.enqueue_trial(trial_params)

    study.optimize(objective, n_trials=n_trials, callbacks=[realtime_callback])
    return study


def plot_contour_subplots(
    X, Y, col, row, level_rol=None, level_row=None, fixed_values=None
):
    if fixed_values is None:
        fixed_values = Constants.get_default_values()

    model = load_ml_model()

    if level_rol is None:
        level_rol = np.linspace(Constants.get_min_values()[col], Constants.get_max_values()[col], RunningConfig.NUM_COLs_ConPLOT).tolist()
    if level_row is None:
        level_row = np.linspace(Constants.get_min_values()[row], Constants.get_max_values()[row], RunningConfig.NUM_ROWS_ConPLOT).tolist()

    n_rows = len(level_row)
    n_cols = len(level_rol)

    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(RunningConfig.NUM_COLs_ConPLOT * 2 * n_cols, RunningConfig.NUM_ROWS_ConPLOT * 2 * n_rows), squeeze=False
    )

    x_range = np.linspace(Constants.get_min_values()[X], Constants.get_max_values()[X], 200)
    y_range = np.linspace(Constants.get_min_values()[Y], Constants.get_max_values()[Y], 200)
    X_grid, Y_grid = np.meshgrid(x_range, y_range)
    n_points = X_grid.size

    for i, r_val in enumerate(level_row):
        for j, c_val in enumerate(level_rol):
            data_dict = {}
            for feat in PostgresConfig.PILOT_COLUMNS:
                if feat == X:
                    data_dict[feat] = X_grid.ravel()
                elif feat == Y:
                    data_dict[feat] = Y_grid.ravel()
                elif feat == col:
                    data_dict[feat] = np.full(n_points, c_val)
                elif feat == row:
                    data_dict[feat] = np.full(n_points, r_val)
                else:
                    data_dict[feat] = np.full(
                        n_points,
                        fixed_values.get(feat, Constants.get_default_values()[feat]),
                    )

            df_input = pd.DataFrame(data_dict, columns=PostgresConfig.PILOT_COLUMNS)

            # print(df_input.head(), flush=True)

            # Z_pred = model.predict(df_input).reshape(X_grid.shape)
            Z_pred = predict_ml_model(df_input, model).reshape(X_grid.shape)
            # print(Z_pred, flush=True)

            ax = axes[i, j]
            contour_filled = ax.contourf(
                X_grid, Y_grid, Z_pred, levels=20, cmap="viridis"
            )
            contour_lines = ax.contour(
                X_grid, Y_grid, Z_pred, levels=20, colors="black", linewidths=0.8
            )
            ax.clabel(contour_lines, inline=True, fontsize=8)

            ax.set_xlabel(X)
            ax.set_ylabel(Y)
            ax.set_title(f"{row} = {r_val:.2f}, {col} = {c_val:.2f}")

            fig.colorbar(contour_filled, ax=ax)

    fig.suptitle("Contour Plot from ML model", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode("utf-8")

    return plot_url


def upload_csv_service(file, form_data):
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(PathConfig.UPLOAD_FOLDER, f"{timestamp}.csv")
    
    file.save(file_path)
    
    df = pd.read_csv(file_path)

    # count columns
    num_columns = len(df.columns)

    # print(f"Number of columns: {num_columns}", flush=True)

    if num_columns < 50:
        ml_model = load_ml_model()

        MAPPED_COLUMNS = PostgresConfig.SENSOR_MAPPINGS

        df = df.rename(columns=MAPPED_COLUMNS)

        df = df[list(MAPPED_COLUMNS.values())]

        df_features = df[PostgresConfig.PILOT_COLUMNS].astype(np.float32)

        predictions = predict_ml_model(df_features, ml_model)
        
        df[PostgresConfig.PREDICTED_OIL] = predictions.astype(float)
    else:
        plrs_model = load_plsr_model()

        # print(f"FTIR model loaded: {plrs_model}", flush=True)

        df = df[PostgresConfig.FTIR_COLUMNS]

        df_features = df[PostgresConfig.FTIR_COLUMNS].astype(np.float32)

        # print(f"FTIR features: {df_features}", flush=True)
        # print(f"FTIR features shape: {df_features.shape}", flush=True)

        predictions = predict_raman(df_features, plrs_model)

        # print(predictions, flush=True)
        # print(predictions.shape, flush=True)

        df[PostgresConfig.PREDICTED_OIL_CONCENTRATION] = predictions.astype(float)
        
    for key, value in form_data.items():
        df[key] = value
    
    if num_columns < 50:
        insert_bulk_to_db(PostgresConfig.TABLE_NAME_PILOT, df)
    else:
        insert_bulk_to_db(PostgresConfig.TABLE_NAME_FTIR, df)

    if HostConfig.HOST_TARGET:
        send_csv_to_another_vm(file_path, form_data)


def process_form_data(form_data):
    X_feature = form_data.get('x_feature')
    Y_feature = form_data.get('y_feature')
    row_feature = form_data.get('row_feature')
    col_feature = form_data.get('col_feature')
    
    data = {
        feature: {
            "min": form_data.get(feature + "_min", "").strip(),
            "max": form_data.get(feature + "_max", "").strip(),
            "fix": form_data.get(feature + "_fix", "").strip(),
        }
        for feature in PostgresConfig.PILOT_COLUMNS
    }

    plot_features = [X_feature, Y_feature, row_feature, col_feature]
    for feature in PostgresConfig.PILOT_COLUMNS:
        if feature in plot_features and data[feature]["fix"] != "":
            return None, f"Feature {feature} was selected for plotting but has a fix value. Please clear this field.", data
        if feature not in plot_features and data[feature]["fix"] == "":
            return None, f"Feature {feature} is not selected for plotting but has no fix value. Please provide a value.", data

    client_fixed = {}
    for feature, vals in data.items():
        if vals["fix"] != "":
            try:
                client_fixed[feature] = float(vals["fix"])
            except ValueError:
                return None, f"Feature {feature}: Invalid Fix value.", data

    plot_img = plot_contour_subplots(
        X=X_feature,
        Y=Y_feature,
        col=col_feature,
        row=row_feature,
        fixed_values=client_fixed,
    )

    return plot_img, None, data


def process_optimization_data(form_data):
    data = {
        feature: {
            "min": form_data.get(feature + "_min", "").strip(),
            "max": form_data.get(feature + "_max", "").strip(),
            "fix": form_data.get(feature + "_fix", "").strip(),
        }
        for feature in PostgresConfig.PILOT_COLUMNS
    }

    variable_features = [f for f, v in data.items() if v["fix"] == ""]
    if len(variable_features) != 4:
        return (
            None,
            None,
            (
                "You must leave exactly 4 Fix boxes empty for the features that will be surveyed "
                "(for example: 2 continuous variables and 2 discrete variables)."
            ),
            data,
        )

    optim_param_ranges = {}
    fixed_params = {}

    for feature, vals in data.items():
        if vals["fix"] == "":
            try:
                optim_param_ranges[feature] = (float(vals["min"]), float(vals["max"]))
            except ValueError:
                return None, None, f"Feature {feature}: Input data error.", data
        else:
            try:
                fixed_params[feature] = float(vals["fix"])
            except ValueError:
                return None, None, f"Feature {feature}: Invalid Fix value.", data

    return optim_param_ranges, fixed_params, None, data


def run_optimization(optim_param_ranges, fixed_params, socketio):
    study = optimize_ml_model(
        optim_param_ranges,
        fixed_params,
        PostgresConfig.PILOT_COLUMNS,
        socketio,
        n_trials=RunningConfig.NUM_TRIALS_BO,
        doe_intervals=RunningConfig.LEVEL_BO_DOE
    )

    socketio.emit(
        "optimization_complete",
        {"best_params": study.best_params, "best_value": study.best_value},
    )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def check_login(username, password):
    error, next_page = None, None

    username, password = hash256(username), hash256(password)
    
    if username in UserConfig.UserDBInstance and UserConfig.UserDBInstance[username] == password:
        session['username'] = username

        next_page = request.args.get('next')
    else:
        error = "Login failure!"

    return next_page, error
    
def hash256(input_string):
    encoded_string = input_string.encode('utf-8')
    hash_object = hashlib.sha256(encoded_string)
    hash_hex = hash_object.hexdigest()
    return hash_hex

def send_csv_to_another_vm(file_path, form_data):
    try:
        files = {'file': open(file_path, 'rb')}
        
        data = {**form_data}
        
        if 'source_vm' not in data:
            data['source_vm'] = HostConfig.HOST_IP
        
        headers = {
            'Authorization': f'Bearer {KeyConfig.API_KEY}'
        }
        
        response = requests.post(
            f"http://{HostConfig.HOST_TARGET}/{RouterConfig.ROUTE_RECEIVE_CSV}", 
            files=files, 
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ File {file_path} successfully sent to remote VM")
            return True
        else:
            print(f"❌ Failed to send file to remote VM. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending file to remote VM: {e}")
        return False
    
def generate_plot(spectrum_df):
    raman_cols = [str(col) for col in range(int(PostgresConfig.FTIR_MIN_COLUMN), int(PostgresConfig.FTIR_MAX_COLUMN) + 1)]
    spectrum_df = spectrum_df[raman_cols]

    # print(spectrum_df)

    plt.figure(figsize=(10, 6))
    
    spectrum_df.columns = [int(col) for col in spectrum_df.columns]
    spectrum_df = spectrum_df.reindex(sorted(spectrum_df.columns, reverse=True), axis=1)
    
    x_values = np.linspace(PostgresConfig.FTIR_MIN_COLUMN, int(PostgresConfig.FTIR_MAX_COLUMN), num=spectrum_df.shape[1])
    
    for i in range(spectrum_df.shape[0]):
        plt.plot(x_values, spectrum_df.iloc[i])
    
    plt.title('Experimental Raman Spectra')
    plt.xlabel('Wavenumber (cm$^{-1}$)')
    plt.ylabel('Intensity (a.u.)')
    plt.grid(True)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_data
def start_streaming(batch_id, session_id, active_streams, socketio):
    previous_data = {'dataframe': None, 'last_timestamp': None}
    
    try:
        while session_id in active_streams and active_streams[session_id]:
            try:
                new_df = fetch_new_data_by_batch_id(batch_id, previous_data.get('last_timestamp'))
                
                if not new_df.empty:
                    if previous_data.get('dataframe') is not None:
                        combined_df = pd.concat([previous_data['dataframe'], new_df], ignore_index=True)
                    else:
                        combined_df = new_df

                    if len(combined_df) > 300:
                        combined_df = combined_df.sort_values('timestamp', ascending=False).head(300).reset_index(drop=True)
                    
                    last_timestamp = combined_df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
                    
                    previous_data['dataframe'] = combined_df
                    previous_data['last_timestamp'] = last_timestamp
                    
                    img_data = generate_plot(combined_df)
                    sample_count = len(combined_df)
                    
                    # Prepare timestamp and concentration data for the chart
                    # Sort by timestamp to ensure chronological order
                    sorted_df = combined_df.sort_values('timestamp')
                    
                    timestamps = sorted_df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist()
                    concentrations = sorted_df[PostgresConfig.PREDICTED_OIL_CONCENTRATION].tolist()
                    
                    socketio.emit('update_data', {
                        'image': img_data, 
                        'count': sample_count,
                        'timestamp': previous_data['last_timestamp'],
                        'timestamps': timestamps,
                        'concentrations': concentrations
                    }, room=session_id)
                elif previous_data.get('dataframe') is not None:
                    img_data = generate_plot(previous_data['dataframe'])
                    sample_count = len(previous_data['dataframe'])
                    
                    sorted_df = previous_data['dataframe'].sort_values('timestamp')
                    timestamps = sorted_df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist()
                    concentrations = sorted_df[PostgresConfig.PREDICTED_OIL_CONCENTRATION].tolist()
                    
                    socketio.emit('update_data', {
                        'image': img_data, 
                        'count': sample_count,
                        'timestamp': previous_data.get('last_timestamp', 'No new updates'),
                        'timestamps': timestamps,
                        'concentrations': concentrations
                    }, room=session_id)
                else:
                    socketio.emit('no_data', {'message': f'No data found for batch ID: {batch_id}'}, room=session_id)
            
            except Exception as e:
                socketio.emit('error', {'message': str(e)}, room=session_id)
            
            time.sleep(5)

    finally:
        if 'dataframe' in previous_data:
            previous_data['dataframe'] = None
        previous_data.clear()
        
        gc.collect()

def raman_plot_in_range(batch_id, start_time, end_time):
    start_time = datetime.fromisoformat(start_time)
    end_time = datetime.fromisoformat(end_time)

    df = fetch_raman_data(batch_id, start_time, end_time)
    error = None

    if df.empty:
        error = 'No data found for the specified parameters'

        return df, None, error

    plot_image = generate_plot(df)

    return df, plot_image, None