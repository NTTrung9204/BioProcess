from flask import Blueprint, request, render_template, jsonify
from app.services.auth_service import login_required
from app.services.query_service import executive_query

query_bp = Blueprint('query', __name__, url_prefix='/query')

@query_bp.route('/', methods=["GET"])
@login_required
def get_query():
    return render_template("query.html")

@query_bp.route('/', methods=["POST"])
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