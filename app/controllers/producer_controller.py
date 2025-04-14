from flask import Blueprint, request, render_template, jsonify
from app.services.auth_service import login_required
from app.utils.app_state import get_producer_running, set_producer_running, get_server_start_time, get_server_uptime

producer_bp = Blueprint('producer', __name__, url_prefix='/producer')

@producer_bp.route('/toggle', methods=["GET"])
@login_required
def toggle_view():
    return render_template("toggle_producer.html")

@producer_bp.route('/status', methods=["GET"])
@login_required
def get_status():
    start_time = get_server_start_time()
    uptime = get_server_uptime()
    
    return jsonify({
        "producer_running": get_producer_running(),
        'status': 'running',
        'start_time': start_time.isoformat(),
        'uptime': uptime
    }) 

@producer_bp.route('/toggle-producer', methods=["POST"])
@login_required
def toggle_producer():
    data = request.json
    if "status" in data:
        status = data["status"]
        set_producer_running(status)
        return (
            jsonify(
                {"message": f"Producer {'started' if status else 'stopped'}"}
            ),
            200,
        )
    return jsonify({"error": "Missing 'status' field"}), 400