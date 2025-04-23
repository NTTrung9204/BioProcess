from flask import Blueprint, request, render_template, jsonify
from app.services.raman_service import raman_plot_in_range
from app.services.auth_service import login_required
from app.services.streaming_service import start_streaming
import threading
import gc

raman_bp = Blueprint('raman', __name__, url_prefix='/raman')

# Dictionary to track active streaming sessions
active_streams = {}

@raman_bp.route('/')
def raman_form():
    return render_template('raman.html')

@raman_bp.route('/process_batch', methods=['POST'])
def process_batch():
    batch_id = request.form.get('batch_id')
    session_id = request.form.get('session_id')
    
    if not batch_id:
        return jsonify({'error': 'Batch ID is required'}), 400
    
    return jsonify({'message': 'Processing started', 'batch_id': batch_id}), 200

@raman_bp.route('/plot', methods=['GET', 'POST'])
def raman_plot():
    if request.method == 'GET':
        return render_template('raman_plot.html')
    
    elif request.method == 'POST':
        print("POST request received", flush=True)
        try:
            batch_id = request.form.get('batch_id')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            print(f"Batch ID: {batch_id}, Start Time: {start_time}, End Time: {end_time}", flush=True)

            if not all([batch_id, start_time, end_time]):
                return jsonify({
                    'error': 'Please provide batch ID, start time, and end time'
                }), 400

            print(f"Batch ID: {batch_id}, Start Time: {start_time}, End Time: {end_time}", flush=True)
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

# Socket.IO handlers will be registered in app.py
def register_socket_handlers(socketio):
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