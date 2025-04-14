from flask import Blueprint, request, jsonify
from app.services.customer_service import get_customers_service, get_customer_service, search_customers_service
from app.services.query_service import executive_query
from app.services.upload_service import upload_csv_service
from app.services.auth_service import login_required
import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/customers', methods=['GET'])
@login_required
def api_get_customers():
    customers = get_customers_service()
    return jsonify({"success": True, "customers": customers})

@api_bp.route('/customers/<cust_name>', methods=['GET'])
@login_required
def api_get_customer(cust_name):
    customer = get_customer_service(cust_name)
    if customer:
        return jsonify({"success": True, "customer": customer})
    else:
        return jsonify({"success": False, "message": "Customer not found"}), 404

@api_bp.route('/search-customers')
def search_customers():
    search_term = request.args.get('term', '')
    customers = search_customers_service(search_term)
    return jsonify(customers)

