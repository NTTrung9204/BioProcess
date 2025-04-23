from flask import Blueprint, request, render_template, jsonify
from app.services.auth_service import login_required
from app.services.upload_service import upload_csv_service
from app.config import PostgresConfig, KeyConfig
from app.services.hash_service import hash256

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

@upload_bp.route('/', methods=["GET"])
@login_required
def upload_csv_page():
    columns = []
    
    for column_def in PostgresConfig._COMMON_COLUMNS:
        parts = column_def.split()

        if PostgresConfig.TIMESTAMP in column_def:
            continue
            
        column_name = parts[0] 
        column_type = parts[1]  
        
        columns.append({
            "name": column_name, 
            "type": column_type
        })
    
    return render_template('upload.html', columns=columns)

@upload_bp.route('/', methods=["POST"])
@login_required
def upload_csv_view():
    if "file" not in request.files:
        return jsonify({"error": "File not found"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Invalid file"}), 400

    try:
        form_data = {key: value for key, value in request.form.items()}
        json_message, status_code, success = upload_csv_service(file, form_data)

        return json_message, status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500 
    
@upload_bp.route('/receive-csv', methods=["POST"])
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