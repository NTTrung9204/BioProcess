from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services.operator_service import (
    get_operators_service, 
    get_operator_service, 
    add_operator_service, 
    update_operator_service, 
    delete_operator_service
)
from app.services.auth_service import login_required

operator_bp = Blueprint('operator', __name__, url_prefix='/operators')

@operator_bp.route('/', methods=['GET'])
@login_required
def operators_page():
    operators = get_operators_service()
    return render_template('operators.html', operators=operators)

@operator_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_operator_page():
    if request.method == 'POST':
        operator_name = request.form.get('operator_name', '')
        level = request.form.get('level', '')
        
        success, message = add_operator_service(operator_name, level)
        
        if success:
            flash('Operator added successfully!', 'success')
            return redirect(url_for('operator.operators_page'))
        else:
            return render_template('add_operator.html', error=message, 
                                  operator_name=operator_name, 
                                  level=level)
    
    return render_template('add_operator.html')

@operator_bp.route('/edit/<operator_name>', methods=['GET', 'POST'])
@login_required
def edit_operator_page(operator_name):
    operator = get_operator_service(operator_name)
    if not operator:
        flash('Operator not found!', 'danger')
        return redirect(url_for('operator.operators_page'))
    
    if request.method == 'POST':
        level = request.form.get('level', '')
        
        success, message = update_operator_service(operator_name, level)
        
        if success:
            flash('Operator updated successfully!', 'success')
            return redirect(url_for('operator.operators_page'))
        else:
            return render_template('edit_operator.html', operator=operator, error=message)
    
    return render_template('edit_operator.html', operator=operator)

@operator_bp.route('/delete/<operator_name>', methods=['POST'])
@login_required
def delete_operator_page(operator_name):
    result, message = delete_operator_service(operator_name)
    if result:
        flash('Operator deleted successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('operator.operators_page')) 