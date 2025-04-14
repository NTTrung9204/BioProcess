from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash, session
from app.services.contour_service import process_form_data
from app.services.optimization_service import process_optimization_data, run_optimization
from app.config import PostgresConfig
from app.constants import Constants
from app.services.auth_service import login_required
import threading
import optuna
import numpy as np
import time

# Biến này sẽ được gán trong hàm register_socket_handlers
socketio = None

# Blueprint for optimization routes
optimization_bp = Blueprint('optimization', __name__)

def register_socket_handlers(socket_io):
    """
    Register socket handlers for optimization events
    """
    global socketio
    socketio = socket_io

@optimization_bp.route('/contour_plot', methods=["GET", "POST"])
@login_required
def contour_plot():
    if request.method == "POST":
        x_feature = request.form.get('x_feature')
        y_feature = request.form.get('y_feature')
        row_feature = request.form.get('row_feature')
        col_feature = request.form.get('col_feature')
        
        selected_features = [x_feature, y_feature, row_feature, col_feature]
        if len(selected_features) != len(set(selected_features)) or '' in selected_features:
            data = {
                feature: {
                    "min": request.form.get(feature + "_min", "").strip(),
                    "max": request.form.get(feature + "_max", "").strip(),
                    "fix": request.form.get(feature + "_fix", "").strip(),
                }
                for feature in PostgresConfig.PILOT_COLUMNS
            }
            return render_template(
                "contour_plot.html", 
                error="Select four different features for X, Y, row, and col.", 
                data=data,
                features=PostgresConfig.PILOT_COLUMNS,
                default_fixed_values=Constants.get_default_values(),
                selected={"x": x_feature, "y": y_feature, "row": row_feature, "col": col_feature}
            )
        
        plot_img, error, data = process_form_data(request.form)

        if error:
            return render_template(
                "contour_plot.html", 
                error=error, 
                data=data,
                features=PostgresConfig.PILOT_COLUMNS,
                default_fixed_values=Constants.get_default_values(),
                selected={"x": x_feature, "y": y_feature, "row": row_feature, "col": col_feature}
            )

        return render_template(
            "contour_plot.html", 
            plot_url=plot_img, 
            data=data,
            features=PostgresConfig.PILOT_COLUMNS,
            default_fixed_values=Constants.get_default_values(),
            selected={"x": x_feature, "y": y_feature, "row": row_feature, "col": col_feature}
        )

    data = {}
    for feature in PostgresConfig.PILOT_COLUMNS:
        data[feature] = {
            "min": Constants.get_min_values().get(feature, ""),
            "max": Constants.get_max_values().get(feature, ""),
            "fix": Constants.get_default_values().get(feature, "")
        }
        
    return render_template(
        "contour_plot.html", 
        data=data,
        features=PostgresConfig.PILOT_COLUMNS,
        default_fixed_values=Constants.get_default_values(),
        selected=None
    )

@optimization_bp.route('/bayesian_optimization', methods=["GET", "POST"])
@login_required
def bayesian_optimization():
    if request.method == "POST":
        feature_1 = request.form.get('feature_1')
        feature_2 = request.form.get('feature_2')
        feature_3 = request.form.get('feature_3')
        feature_4 = request.form.get('feature_4')
    
        optim_param_ranges, fixed_params, error, data = process_optimization_data(request.form)

        if error:
            return render_template(
                "bayesian_optimization.html", 
                error=error, 
                data=data,         
                features=PostgresConfig.PILOT_COLUMNS,
                default_fixed_values=Constants.get_default_values(),
                selected={"f1": feature_1, "f2": feature_2, "f3": feature_3, "f4": feature_4}
            )

        thread = threading.Thread(target=run_optimization, args=(optim_param_ranges, fixed_params, socketio))
        thread.start()

        return render_template(
            "bayesian_optimization.html",
            data=data,
            features=PostgresConfig.PILOT_COLUMNS,
            default_fixed_values=Constants.get_default_values(),
            selected={"f1": feature_1, "f2": feature_2, "f3": feature_3, "f4": feature_4},
            message="Running optimization. Please monitor the real-time chart on the right.",
        )

    data = {}
    for feature in PostgresConfig.PILOT_COLUMNS:
        data[feature] = {
            "min": Constants.get_min_values().get(feature, ""),
            "max": Constants.get_max_values().get(feature, ""),
            "fix": Constants.get_default_values().get(feature, "")
        }
    
    return render_template(
        "bayesian_optimization.html", 
        data=data,
        features=PostgresConfig.PILOT_COLUMNS,
        default_fixed_values=Constants.get_default_values(),
        selected=None
    )
