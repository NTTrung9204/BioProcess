from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from app.services.customer_service import get_customers_service, get_customer_service, add_customer_service, update_customer_service, delete_customer_service
from app.services.auth_service import login_required

customer_bp = Blueprint('customer', __name__, url_prefix='/customers')

@customer_bp.route('/', methods=['GET'])
@login_required
def customers_page():
    customers = get_customers_service()
    return render_template('customers.html', customers=customers)

@customer_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer_page():
    if request.method == 'POST':
        cust_name = request.form.get('cust_name', '')
        contact_infor = request.form.get('contact_infor', '')
        address = request.form.get('address', '')
        country = request.form.get('country', '')
        
        success, message = add_customer_service(cust_name, contact_infor, address, country)
        
        if success:
            return redirect(url_for('customer.customers_page'))
        else:
            return render_template('add_customer.html', error=message, 
                                  cust_name=cust_name, 
                                  contact_infor=contact_infor, 
                                  address=address, 
                                  country=country)
    
    return render_template('add_customer.html')

@customer_bp.route('/edit/<cust_name>', methods=['GET', 'POST'])
@login_required
def edit_customer_page(cust_name):
    customer = get_customer_service(cust_name)
    if not customer:
        return redirect(url_for('customer.customers_page'))
    
    if request.method == 'POST':
        contact_infor = request.form.get('contact_infor', '')
        address = request.form.get('address', '')
        country = request.form.get('country', '')
        
        success, message = update_customer_service(cust_name, contact_infor, address, country)
        
        if success:
            return redirect(url_for('customer.customers_page'))
        else:
            return render_template('edit_customer.html', customer=customer, error=message)
    
    return render_template('edit_customer.html', customer=customer)

@customer_bp.route('/delete/<cust_name>', methods=['GET', 'POST'])
@login_required
def delete_customer_page(cust_name):
    if request.method == 'POST':
        result, message = delete_customer_service(cust_name)
        if result:
            flash('Customer deleted successfully!', 'success')
            return redirect(url_for('customer.customers_page'))
        else:
            flash(message, 'danger')
            return redirect(url_for('customer.customers_page'))
    
    customer = get_customer_service(cust_name)
    if not customer:
        flash('Customer not found!', 'danger')
        return redirect(url_for('customer.customers_page'))
        
    return render_template('delete_customer.html', customer=customer) 