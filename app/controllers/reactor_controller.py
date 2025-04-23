from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services.reactor_service import (
    get_reactors_service, 
    get_reactor_service, 
    add_reactor_service, 
    update_reactor_service, 
    delete_reactor_service
)
from app.services.auth_service import login_required
from datetime import datetime

reactor_bp = Blueprint('reactor', __name__, url_prefix='/reactors')

@reactor_bp.route('/', methods=['GET'])
@login_required
def reactors_page():
    reactors = get_reactors_service()
    return render_template('reactors.html', reactors=reactors)

@reactor_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_reactor_page():
    if request.method == 'POST':
        reactor_name = request.form.get('reactor_name', '')
        maintenance_day = request.form.get('maintenance_day', '')
        
        success, message = add_reactor_service(reactor_name, maintenance_day)
        
        if success:
            flash('Reactor added successfully!', 'success')
            return redirect(url_for('reactor.reactors_page'))
        else:
            return render_template('add_reactor.html', error=message, 
                                  reactor_name=reactor_name, 
                                  maintenance_day=maintenance_day)
    
    return render_template('add_reactor.html')

@reactor_bp.route('/edit/<reactor_name>', methods=['GET', 'POST'])
@login_required
def edit_reactor_page(reactor_name):
    reactor = get_reactor_service(reactor_name)
    if not reactor:
        flash('Reactor not found!', 'danger')
        return redirect(url_for('reactor.reactors_page'))
    
    if request.method == 'POST':
        maintenance_day = request.form.get('maintenance_day', '')
        
        success, message = update_reactor_service(reactor_name, maintenance_day)
        
        if success:
            flash('Reactor updated successfully!', 'success')
            return redirect(url_for('reactor.reactors_page'))
        else:
            return render_template('edit_reactor.html', reactor=reactor, error=message)
    
    return render_template('edit_reactor.html', reactor=reactor)

@reactor_bp.route('/delete/<reactor_name>', methods=['POST'])
@login_required
def delete_reactor_page(reactor_name):
    result, message = delete_reactor_service(reactor_name)
    if result:
        flash('Reactor deleted successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('reactor.reactors_page')) 