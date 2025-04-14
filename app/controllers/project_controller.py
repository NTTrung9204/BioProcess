from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from app.services.project_service import get_projects_service, get_project_service, add_project_service, update_project_service, delete_project_service
from app.services.customer_service import get_customers_service
from app.services.auth_service import login_required

project_bp = Blueprint('project', __name__, url_prefix='/projects')

@project_bp.route('/')
@login_required
def projects():
    projects_list = get_projects_service()
    return render_template('projects.html', projects=projects_list)

@project_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_project():
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        budget = request.form.get('budget')
        project_manager = request.form.get('project_manager')
        cust_name = request.form.get('cust_name')
        
        result, message = add_project_service(project_name, budget, project_manager, cust_name)
        
        if result:
            flash('Project added successfully!', 'success')
            return redirect(url_for('project.projects'))
        else:
            flash(message, 'danger')
    
    customers = get_customers_service()
    return render_template('add_project.html', customers=customers)

@project_bp.route('/edit/<project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        budget = request.form.get('budget')
        project_manager = request.form.get('project_manager')
        cust_name = request.form.get('cust_name')
        
        success, message = update_project_service(project_id, project_name, budget, project_manager, cust_name)
        
        if success:
            flash('Project updated successfully', 'success')
            return redirect(url_for('project.projects'))
        else:
            flash(message, 'error')
            return redirect(url_for('project.edit_project', project_id=project_id))
    else:
        project = get_project_service(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('project.projects'))
            
        customers = get_customers_service()
        return render_template('edit_project.html', project=project, customers=customers)

@project_bp.route('/delete/<project_id>', methods=['GET', 'POST'])
@login_required
def delete_project(project_id):
    if request.method == 'POST':
        result, message = delete_project_service(project_id)
        if result:
            flash('Project deleted successfully!', 'success')
            return redirect(url_for('project.projects'))
        else:
            flash(message, 'danger')
            return redirect(url_for('project.projects'))
    
    project = get_project_service(project_id)
    if not project:
        flash('Project not found!', 'danger')
        return redirect(url_for('project.projects'))
        
    return render_template('delete_project.html', project=project) 