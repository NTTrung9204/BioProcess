import base64
import io
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from app.utils import load_ml_model, predict_ml_model
from app.config import PostgresConfig, RunningConfig
from app.constants import Constants

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

            Z_pred = predict_ml_model(df_input, model).reshape(X_grid.shape)

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

    fig.suptitle("RESULTS from ML model", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode("utf-8")

    return plot_url 