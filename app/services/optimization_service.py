import itertools
import numpy as np
import optuna
import pandas as pd
import threading
from app.config import PostgresConfig, RunningConfig
from app.utils import load_ml_model, predict_ml_model

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
    print("Starting optimization...", flush=True)
    try:
        study = optimize_ml_model(
            optim_param_ranges,
            fixed_params,
            PostgresConfig.PILOT_COLUMNS,
            socketio,
            n_trials=RunningConfig.NUM_TRIALS_BO,
            doe_intervals=RunningConfig.LEVEL_BO_DOE
        )

        if socketio is not None and hasattr(socketio, 'emit'):
            try:
                socketio.emit(
                    "optimization_complete",
                    {"best_params": study.best_params, "best_value": study.best_value},
                )
                print(f"Optimization complete! Best value: {study.best_value}", flush=True)
            except Exception as e:
                print(f"Error emitting optimization complete: {e}", flush=True)
        return study
    except Exception as e:
        print(f"Error during optimization: {e}", flush=True)
        if socketio is not None and hasattr(socketio, 'emit'):
            try:
                socketio.emit(
                    "optimization_error",
                    {"error": str(e)},
                )
            except Exception as e2:
                print(f"Error emitting optimization error: {e2}", flush=True)
        return None

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
        features = {}
        for col in columns:
            if col in optim_param_ranges:
                low, high = optim_param_ranges[col]
                value = trial.suggest_float(col, low, high)
            else:
                value = fixed_params[col]
            features[col] = value
        features_array = pd.DataFrame([features], columns=columns)
        pred = predict_ml_model(features_array, model)
        return pred[0][0]

    def realtime_callback(study, trial):
        if trial.value is not None and socketio is not None and hasattr(socketio, 'emit'):
            try:
                socketio.emit(
                    "trial_update",
                    {"trial": trial.number, "params": trial.params, "value": trial.value},
                )
            except Exception as e:
                print(f"Error emitting trial update: {e}", flush=True)

    study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(n_startup_trials=10)
    )

    doe_trials = generate_doe_trials(optim_param_ranges, num_intervals=doe_intervals)
    for trial_params in doe_trials:
        study.enqueue_trial(trial_params)

    study.optimize(objective, n_trials=n_trials, callbacks=[realtime_callback])
    return study 