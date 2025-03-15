from flask import Flask, request, jsonify, render_template
import os
import threading
import time
from flask_socketio import SocketIO

from config import HostConfig, RouterConfig, PathConfig, PostgresConfig

from repositories import create_table
from services import consume_kafka, process_form_data, process_optimization_data, produce_data, run_optimization, upload_csv_service

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")

os.makedirs(PathConfig.UPLOAD_FOLDER, exist_ok=True)

producer_running = True

@app.route(f"/{RouterConfig.ROUTE_PRODUCER_STATUS}", methods=["GET"])
def get_status():
    return jsonify({"producer_running": producer_running})

@app.route(f"/{RouterConfig.ROUTE_TOGGLE_PRODUCER}")
def toggle_view():
    return render_template("toggle_producer.html")

@app.route(f"/{RouterConfig.ROUTE_TOGGLE_PRODUCER}", methods=["POST"])
def toggle_producer():
    global producer_running
    data = request.json
    if "status" in data:
        producer_running = data["status"]
        return (
            jsonify(
                {"message": f"Producer {'started' if producer_running else 'stopped'}"}
            ),
            200,
        )
    return jsonify({"error": "Missing 'status' field"}), 400

@app.route(f"/{RouterConfig.ROUTE_UPLOAD}", methods=["POST"])
def upload_csv_view():
    if "file" not in request.files:
        return jsonify({"error": "File not found"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Invalid file"}), 400

    try:
        upload_csv_service(request, file)

        return jsonify(
            {
                "message": "Upload successful and data has been inserted into the database!"
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route(f"/{RouterConfig.ROUTE_UPLOAD}")
def upload_page():
    return render_template("upload.html")

@app.route(f"/{RouterConfig.ROUTE_CONTOUR_PLOT}", methods=["GET", "POST"])
def contour_plot():
    if request.method == "POST":
        plot_img, error, data = process_form_data(request.form)

        if error:
            return render_template("contour_plot.html", error=error, data=data)

        return render_template("contour_plot.html", plot_url=plot_img, data=data)

    data = {feature: {"min": "", "max": "", "fix": ""} for feature in PostgresConfig.FEATURES}
    return render_template("contour_plot.html", data=data)

@app.route(f"/{RouterConfig.ROUTE_BAYESIAN_OPTIMAZATION}", methods=["GET", "POST"])
def bayesian_optimazation():
    if request.method == "POST":
        optim_param_ranges, fixed_params, error, data = process_optimization_data(request.form)

        if error:
            return render_template("bayesian_optimazation.html", error=error, data=data)

        thread = threading.Thread(target=run_optimization, args=(optim_param_ranges, fixed_params, socketio))
        thread.start()

        return render_template(
            "bayesian_optimazation.html",
            data=data,
            message="Running optimization. Please monitor the real-time chart on the right.",
        )

    data = {feature: {"min": "", "max": "", "fix": ""} for feature in PostgresConfig.FEATURES}
    return render_template("bayesian_optimazation.html", data=data)


if __name__ == "__main__":
    time.sleep(10)

    create_table(
        PostgresConfig.TABLE_NAME_OPERATION,
        PostgresConfig.DATABASE_OPERATION_TABLE_COLUMNS,
        PostgresConfig.POSTGRES_CONFIG,
    )
    create_table(
        PostgresConfig.TABLE_NAME_TEMP,
        PostgresConfig.DATABASE_OPERATION_TABLE_COLUMNS,
        PostgresConfig.POSTGRES_CONFIG_TEMP,
    )
    create_table(
        PostgresConfig.TABLE_NAME_RAMAN,
        PostgresConfig.DATABASE_RAMAN_TABLE_COLUMNS,
        PostgresConfig.POSTGRES_CONFIG,
    )

    time.sleep(10)

    threading.Thread(target=produce_data, daemon=True).start()
    threading.Thread(target=consume_kafka, daemon=True).start()

    app.run(host="0.0.0.0", port=int(HostConfig.HOST_PORT), debug=True, use_reloader=False)
