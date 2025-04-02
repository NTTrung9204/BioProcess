import gc
from flask import Flask, redirect, request, jsonify, render_template, session, url_for
import os
import threading
import time
from flask_socketio import SocketIO

from config import HostConfig, RouterConfig, PathConfig, PostgresConfig, KeyConfig

from constants import Constants
from repositories import create_table
from services import check_login, consume_kafka, hash256, login_required, process_form_data, process_optimization_data, produce_data, raman_plot_in_range, run_optimization, start_streaming, upload_csv_service, executive_query

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")

os.makedirs(PathConfig.UPLOAD_FOLDER, exist_ok=True)

producer_running = True
active_streams = {}

@app.route(f"/{RouterConfig.ROUTE_QUERY}", methods=["POST"])
@login_required
def post_query():
    try:
        data = request.json
        custom_query = data.get('query')
        
        result, column_names = executive_query(custom_query)
        
        return jsonify({
            'success': True,
            'columns': column_names,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route(f"/{RouterConfig.ROUTE_QUERY}", methods=["GET"])
@login_required
def get_query():
    return render_template("query.html")

@app.route(f"/{RouterConfig.ROUTE_PRODUCER_STATUS}", methods=["GET"])
@login_required
def get_status():
    return jsonify({"producer_running": producer_running})

@app.route(f"/{RouterConfig.ROUTE_TOGGLE_PRODUCER}")
@login_required
def toggle_view():
    return render_template("toggle_producer.html")

@app.route(f"/{RouterConfig.ROUTE_TOGGLE_PRODUCER}", methods=["POST"])
@login_required
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

@app.route(f"/{RouterConfig.ROUTE_UPLOAD}", methods=["GET"])
@login_required
def upload_csv_page():
    # Parse the column definitions from PostgresConfig._COMMON_COLUMNS
    columns = []
    
    for column_def in PostgresConfig._COMMON_COLUMNS:
        # Extract column name and other attributes from the definition
        # Example format: "TIMESTAMP TIMESTAMP UNIQUE"
        parts = column_def.split()
        if len(parts) < 4:
            continue
            
        column_name = parts[0] 
        column_type = parts[1]  
        
        
        columns.append({
            "name": column_name, 
            "type": column_type
        })
    
    return render_template('upload.html', columns=columns)

@app.route(f"/{RouterConfig.ROUTE_UPLOAD}", methods=["POST"])
@login_required
def upload_csv_view():
    if "file" not in request.files:
        return jsonify({"error": "File not found"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Invalid file"}), 400

    try:
        form_data = {key: value for key, value in request.form.items()}
        upload_csv_service(file, form_data)

        return jsonify(
            {
                "message": "Upload successful and data has been inserted into the database!"
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route(f"/{RouterConfig.ROUTE_CONTOUR_PLOT}", methods=["GET", "POST"])
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
                error="You must select four different features for X, Y, row, and col.", 
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

@app.route(f"/{RouterConfig.ROUTE_BAYESIAN_OPTIMAZATION}", methods=["GET", "POST"])
@login_required
def bayesian_optimazation():
    if request.method == "POST":
        feature_1 = request.form.get('feature_1')
        feature_2 = request.form.get('feature_2')
        feature_3 = request.form.get('feature_3')
        feature_4 = request.form.get('feature_4')
    
        optim_param_ranges, fixed_params, error, data = process_optimization_data(request.form)

        if error:
            return render_template(
                "bayesian_optimazation.html", 
                error=error, 
                data=data,         
                features=PostgresConfig.PILOT_COLUMNS,
                default_fixed_values=Constants.get_default_values(),
                selected={"f1": feature_1, "f2": feature_2, "f3": feature_3, "f4": feature_4}
            )

        thread = threading.Thread(target=run_optimization, args=(optim_param_ranges, fixed_params, socketio))
        thread.start()

        return render_template(
            "bayesian_optimazation.html",
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
        "bayesian_optimazation.html", 
        data=data,
        features=PostgresConfig.PILOT_COLUMNS,
        default_fixed_values=Constants.get_default_values(),
        selected=None
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        next_page, error = check_login(username, password)

        if error:
            return render_template("login.html", error=error)
        else:
            return redirect(next_page or url_for("home"))
        
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route('/')
@login_required
def home():
    return render_template("index.html")

@app.route(f"/{RouterConfig.ROUTE_RECEIVE_CSV}", methods=["POST"])
def receive_csv():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    if hash256(token) != KeyConfig.VERIFIED_API_KEY:
        return jsonify({"error": "Invalid API key"}), 403
    
    if 'file' not in request.files:
        return jsonify({"error": "File not found"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Invalid file"}), 400
    
    form_data = {key: value for key, value in request.form.items()}
    
    source_vm = request.form.get("source_vm")
    
    if not form_data:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        upload_csv_service(file, form_data)
        
        return jsonify({
            "message": "File received and processed successfully",
            "source_vm": source_vm
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/raman')
def raman_form():
    return render_template('raman.html')

@app.route('/process_batch', methods=['POST'])
def process_batch():
    batch_id = request.form.get('batch_id')
    session_id = request.form.get('session_id')
    
    if not batch_id:
        return jsonify({'error': 'Batch ID is required'}), 400
    
    return jsonify({'message': 'Processing started', 'batch_id': batch_id}), 200

@app.route('/raman_plot', methods=['GET', 'POST'])
def raman_plot():
    print(active_streams, flush=True)
    if request.method == 'GET':
        return render_template('raman_plot.html')
    
    elif request.method == 'POST':
        try:
            batch_id = request.form.get('batch_id')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')

            if not all([batch_id, start_time, end_time]):
                return jsonify({
                    'error': 'Please provide batch ID, start time, and end time'
                }), 400

            df, plot_image, error = raman_plot_in_range(batch_id, start_time, end_time)

            if error:
                return jsonify({
                    'error': error
                }), 404

            return jsonify({
                'image': plot_image,
                'sample_count': len(df),
                'start_time': str(start_time),
                'end_time': str(end_time)
            })

        except Exception as e:
            return jsonify({
                'error': f'An error occurred: {str(e)}'
            }), 500

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('start_streaming')
def handle_start_streaming(data):
    batch_id = data.get('batch_id')
    session_id = request.sid
    
    active_streams[session_id] = True
    thread = threading.Thread(target=start_streaming, args=(batch_id, session_id, active_streams, socketio))
    thread.daemon = True
    thread.start()

@socketio.on('stop_streaming')
def handle_stop_streaming():
    session_id = request.sid
    if session_id in active_streams:
        active_streams[session_id] = False
        del active_streams[session_id]

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in active_streams:
        active_streams[session_id] = False
        del active_streams[session_id]
    gc.collect()
    print(f"Client disconnected: {session_id}")

if __name__ == "__main__":
    time.sleep(2)

    create_table(
        PostgresConfig.TABLE_NAME_PILOT,
        PostgresConfig.DATABASE_PILOT_TABLE_COLUMNS,
        PostgresConfig.POSTGRES_CONFIG,
    )
    create_table(
        PostgresConfig.TABLE_NAME_TEMP,
        PostgresConfig.DATABASE_PILOT_TABLE_COLUMNS,
        PostgresConfig.POSTGRES_CONFIG_TEMP,
    )
    create_table(
        PostgresConfig.TABLE_NAME_FTIR,
        PostgresConfig.DATABASE_FTIR_TABLE_COLUMNS,
        PostgresConfig.POSTGRES_CONFIG,
    )

    # print(PostgresConfig.SENSOR_MAPPINGS, flush=True)
    # print(PostgresConfig.DATABASE_PILOT_TABLE_COLUMNS, flush=True)
    # print(PostgresConfig.DATABASE_FTIR_TABLE_COLUMNS, flush=True)

    # print(Constants.get_default_values(), flush=True)
    # print(Constants.get_min_values(), flush=True)
    # print(Constants.get_max_values(), flush=True)


    time.sleep(2)

    threading.Thread(target=produce_data, daemon=True).start()
    threading.Thread(target=consume_kafka, daemon=True).start()

    app.run(host="0.0.0.0", port=int(HostConfig.HOST_PORT), debug=True, use_reloader=False)
