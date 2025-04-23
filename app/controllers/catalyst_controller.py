from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services.catalyst_service import (
    get_catalysts_service, 
    get_catalyst_service, 
    add_catalyst_service, 
    update_catalyst_service, 
    delete_catalyst_service
)
from app.services.auth_service import login_required

catalyst_bp = Blueprint('catalyst', __name__, url_prefix='/catalysts')

@catalyst_bp.route('/', methods=['GET'])
@login_required
def catalysts_page():
    catalysts = get_catalysts_service()
    return render_template('catalysts.html', catalysts=catalysts)

@catalyst_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_catalyst_page():
    if request.method == 'POST':
        catalyst_name = request.form.get('catalyst_name', '')
        provider = request.form.get('provider', '')
        
        success, message = add_catalyst_service(catalyst_name, provider)
        
        if success:
            flash('Catalyst added successfully!', 'success')
            return redirect(url_for('catalyst.catalysts_page'))
        else:
            return render_template('add_catalyst.html', error=message, 
                                  catalyst_name=catalyst_name, 
                                  provider=provider)
    
    return render_template('add_catalyst.html')

@catalyst_bp.route('/edit/<catalyst_name>', methods=['GET', 'POST'])
@login_required
def edit_catalyst_page(catalyst_name):
    catalyst = get_catalyst_service(catalyst_name)
    if not catalyst:
        flash('Catalyst not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    if request.method == 'POST':
        provider = request.form.get('provider', '')
        
        success, message = update_catalyst_service(catalyst_name, provider)
        
        if success:
            flash('Catalyst updated successfully!', 'success')
            return redirect(url_for('catalyst.catalysts_page'))
        else:
            return render_template('edit_catalyst.html', catalyst=catalyst, error=message)
    
    return render_template('edit_catalyst.html', catalyst=catalyst)

@catalyst_bp.route('/delete/<catalyst_name>', methods=['POST'])
@login_required
def delete_catalyst_page(catalyst_name):
    result, message = delete_catalyst_service(catalyst_name)
    if result:
        flash('Catalyst deleted successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('catalyst.catalysts_page')) 