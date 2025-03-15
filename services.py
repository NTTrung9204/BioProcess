import base64
from datetime import datetime
import io
import itertools
import json
import os
import time
from kafka import KafkaConsumer, KafkaProducer
from matplotlib import pyplot as plt
import numpy as np
import optuna
import pandas as pd
from config import KafkaConfig, PathConfig, PostgresConfig
from constants import DEFAULT_FIXED_BY_MEAN_VALUE, MAX_VALUES, MIN_VALUES
from repositories import fetch_data, insert_bulk_to_db, insert_data_to_db
from utils import (
    get_producer_status,
    load_plsr_model,
    load_scaler,
    load_xgboost_model,
    map_record,
    predict_raman,
    predict_xgb,
)


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

            producer.send(KafkaConfig.KAFKA_TOPIC_OPERATION, value=mapped_record)

            print(
                f"Produced Operation: {record['timestamp']} | Scan: {scan}", flush=True
            )

            scan += 1
            time.sleep(2)


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

        xgboost_model = load_xgboost_model()
        plsr_model = load_plsr_model()

        scaler_x = load_scaler(PathConfig.SCALER_X)
        scaler_y = load_scaler(PathConfig.SCALER_Y)

        for message in consumer:
            data = message.value

            if PostgresConfig.SCAN not in data or data[PostgresConfig.SCAN] is None:
                data[PostgresConfig.SCAN] = "empty_scan"

            if message.topic == KafkaConfig.KAFKA_TOPIC_OPERATION:
                if PostgresConfig.CUST not in data or data[PostgresConfig.CUST] is None:
                    data[PostgresConfig.CUST] = "empty_cust"

                if (
                    PostgresConfig.PROJECT_ID not in data
                    or data[PostgresConfig.PROJECT_ID] is None
                ):
                    data[PostgresConfig.PROJECT_ID] = "empty_project_id"

                if (
                    PostgresConfig.BATCH_ID not in data
                    or data[PostgresConfig.BATCH_ID] is None
                ):
                    data[PostgresConfig.BATCH_ID] = "empty_batch_id"

                data[PostgresConfig.PREDICTION] = predict_xgb(data, xgboost_model)

                insert_data_to_db(
                    PostgresConfig.TABLE_NAME_OPERATION, data, xgboost_model
                )
            elif message.topic == KafkaConfig.KAFKA_TOPIC_RAMAN:
                data[PostgresConfig.PREDICTION] = predict_raman(
                    data, plsr_model, scaler_x, scaler_y
                )

                insert_data_to_db(
                    PostgresConfig.TABLE_NAME_RAMAN,
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


def optimize_xgb(
    optim_param_ranges, fixed_params, columns, socketio, n_trials, doe_intervals=4
):
    model = load_xgboost_model()

    def objective(trial):
        features = []
        for col in columns:
            if col in optim_param_ranges:
                low, high = optim_param_ranges[col]
                value = trial.suggest_float(col, low, high)
            else:
                value = fixed_params[col]
            features.append(value)
        features_array = np.array([features])
        pred = model.predict(features_array)
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
        fixed_values = DEFAULT_FIXED_BY_MEAN_VALUE

    model = load_xgboost_model()

    if level_rol is None:
        level_rol = np.linspace(MIN_VALUES[col], MAX_VALUES[col], 4).tolist()
    if level_row is None:
        level_row = np.linspace(MIN_VALUES[row], MAX_VALUES[row], 4).tolist()

    n_rows = len(level_row)
    n_cols = len(level_rol)

    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(8 * n_cols, 8 * n_rows), squeeze=False
    )

    x_range = np.linspace(MIN_VALUES[X], MAX_VALUES[X], 200)
    y_range = np.linspace(MIN_VALUES[Y], MAX_VALUES[Y], 200)
    X_grid, Y_grid = np.meshgrid(x_range, y_range)
    n_points = X_grid.size

    for i, r_val in enumerate(level_row):
        for j, c_val in enumerate(level_rol):
            data_dict = {}
            for feat in PostgresConfig.FEATURES:
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
                        fixed_values.get(feat, DEFAULT_FIXED_BY_MEAN_VALUE[feat]),
                    )

            df_input = pd.DataFrame(data_dict, columns=PostgresConfig.FEATURES)

            Z_pred = model.predict(df_input).reshape(X_grid.shape)

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

    fig.suptitle("Contour Plot from model XGBoost", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode("utf-8")

    return plot_url


def upload_csv_service(request, file):
    xgboost_model = load_xgboost_model()

    cust = request.form["cust"]
    project_id = request.form["project_id"]
    batch_id = request.form["batch_id"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(PathConfig.UPLOAD_FOLDER, f"{timestamp}.csv")

    file.save(file_path)

    df = pd.read_csv(file_path)

    df["cust"] = cust
    df["project_id"] = project_id
    df["batchid"] = batch_id
    df["scan"] = 14

    df_features = df[PostgresConfig.OPERATION_COLUMNS].astype(np.float32)

    predictions = xgboost_model.predict(df_features.to_numpy())

    df["prediction"] = predictions.astype(float)

    data_list = df.to_dict(orient="records")
    insert_bulk_to_db("operation", data_list)


def process_form_data(form_data):
    data = {
        feature: {
            "min": form_data.get(feature + "_min", "").strip(),
            "max": form_data.get(feature + "_max", "").strip(),
            "fix": form_data.get(feature + "_fix", "").strip(),
        }
        for feature in PostgresConfig.FEATURES
    }

    variables = [f for f, v in data.items() if v["fix"] == ""]
    if len(variables) != 4:
        return (
            None,
            "You must leave exactly 4 Fix boxes empty for the features that will be surveyed: 2 continuous variables (X, Y) and 2 discrete variables (col, row).",
            data,
        )

    X_feature, Y_feature, col_feature, row_feature = variables

    client_fixed = {}
    for feature, vals in data.items():
        if vals["fix"] != "":
            try:
                client_fixed[feature] = float(vals["fix"])
            except ValueError:
                return None, f"Feature {feature}: Invalid Fix value.", data

    plot_img = plot_contour_subplots(
        X=row_feature,
        Y=col_feature,
        col=Y_feature,
        row=X_feature,
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
        for feature in PostgresConfig.FEATURES
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
    study = optimize_xgb(
        optim_param_ranges,
        fixed_params,
        PostgresConfig.FEATURES,
        socketio,
        n_trials=1000,
    )

    socketio.emit(
        "optimization_complete",
        {"best_params": study.best_params, "best_value": study.best_value},
    )
