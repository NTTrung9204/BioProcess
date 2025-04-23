from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.services.catalyst_composition_service import (
    get_compositions_service,
    get_composition_service,
    add_composition_service,
    update_composition_service,
    delete_composition_service,
    get_catalyst_with_compositions_service,
    get_remaining_percentage_service,
    search_catalysts_by_name_service
)
from app.services.catalyst_service import get_catalyst_service
from app.services.auth_service import login_required

catalyst_composition_bp = Blueprint('catalyst_composition', __name__, url_prefix='/catalyst-compositions')

# Web routes with UI
@catalyst_composition_bp.route('/manage/<catalyst_id>', methods=['GET'])
@login_required
def manage_compositions_page(catalyst_id):
    """Render the catalyst composition management page"""
    catalyst_data = get_catalyst_with_compositions_service(catalyst_id)
    if not catalyst_data:
        flash('Catalyst not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    remaining_percentage = get_remaining_percentage_service(catalyst_id)
    
    return render_template('catalyst_compositions.html', 
                          catalyst=catalyst_data, 
                          remaining_percentage=remaining_percentage)

@catalyst_composition_bp.route('/add/<catalyst_id>', methods=['GET', 'POST'])
@login_required
def add_composition_page(catalyst_id):
    """Add a new composition to a catalyst"""
    catalyst_data = get_catalyst_with_compositions_service(catalyst_id)
    if not catalyst_data:
        flash('Catalyst not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    if request.method == 'POST':
        composition = request.form.get('composition', '')
        percentage = request.form.get('percentage', '')
        provider = request.form.get('provider', '')
        
        success, message = add_composition_service(catalyst_id, composition, percentage, provider)
        
        if success:
            flash('Composition added successfully!', 'success')
            return redirect(url_for('catalyst_composition.manage_compositions_page', catalyst_id=catalyst_id))
        else:
            return render_template('add_catalyst_composition.html', 
                                  error=message, 
                                  catalyst=catalyst_data,
                                  composition=composition,
                                  percentage=percentage,
                                  provider=provider,
                                  remaining_percentage=get_remaining_percentage_service(catalyst_id))
    
    return render_template('add_catalyst_composition.html', 
                          catalyst=catalyst_data,
                          remaining_percentage=get_remaining_percentage_service(catalyst_id))

@catalyst_composition_bp.route('/edit/<composition_id>', methods=['GET', 'POST'])
@login_required
def edit_composition_page(composition_id):
    """Edit an existing catalyst composition"""
    composition = get_composition_service(composition_id)
    if not composition:
        flash('Composition not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    catalyst_data = get_catalyst_with_compositions_service(composition['catalyst_id'])
    
    if request.method == 'POST':
        composition_name = request.form.get('composition', '')
        percentage = request.form.get('percentage', '')
        provider = request.form.get('provider', '')
        
        success, message = update_composition_service(composition_id, composition_name, percentage, provider)
        
        if success:
            flash('Composition updated successfully!', 'success')
            return redirect(url_for('catalyst_composition.manage_compositions_page', catalyst_id=composition['catalyst_id']))
        else:
            return render_template('edit_catalyst_composition.html', 
                                  error=message, 
                                  catalyst=catalyst_data,
                                  composition=composition,
                                  remaining_percentage=get_remaining_percentage_service(composition['catalyst_id']))
    
    return render_template('edit_catalyst_composition.html', 
                          catalyst=catalyst_data,
                          composition=composition,
                          remaining_percentage=get_remaining_percentage_service(composition['catalyst_id']))

@catalyst_composition_bp.route('/delete/<composition_id>', methods=['POST'])
@login_required
def delete_composition_page(composition_id):
    """Delete a catalyst composition"""
    composition = get_composition_service(composition_id)
    if not composition:
        flash('Composition not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    catalyst_id = composition['catalyst_id']
    
    success, message = delete_composition_service(composition_id)
    
    if success:
        flash('Composition deleted successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('catalyst_composition.manage_compositions_page', catalyst_id=catalyst_id))

@catalyst_composition_bp.route('/search-catalysts', methods=['GET'])
@login_required
def search_catalysts():
    """Search for catalysts by name"""
    search_term = request.args.get('term', '')
    catalysts = search_catalysts_by_name_service(search_term)
    return jsonify(catalysts)

# API routes
@catalyst_composition_bp.route('/api/catalyst/<catalyst_id>/compositions', methods=['GET'])
def get_catalyst_compositions(catalyst_id):
    """Get all compositions for a specific catalyst"""
    compositions = get_compositions_service(catalyst_id)
    return jsonify({
        'status': 'success',
        'data': compositions,
        'remaining_percentage': get_remaining_percentage_service(catalyst_id)
    })

@catalyst_composition_bp.route('/api/catalyst/<catalyst_id>/compositions/full', methods=['GET'])
def get_catalyst_with_compositions(catalyst_id):
    """Get catalyst details with all its compositions"""
    result = get_catalyst_with_compositions_service(catalyst_id)
    if not result:
        return jsonify({'status': 'error', 'message': f'Catalyst with ID {catalyst_id} not found'}), 404
    
    return jsonify({
        'status': 'success',
        'data': result
    })

@catalyst_composition_bp.route('/api/compositions/<composition_id>', methods=['GET'])
def get_composition(composition_id):
    """Get a specific composition by ID"""
    composition = get_composition_service(composition_id)
    if not composition:
        return jsonify({'status': 'error', 'message': f'Composition with ID {composition_id} not found'}), 404
    
    return jsonify({
        'status': 'success',
        'data': composition
    })

@catalyst_composition_bp.route('/api/catalyst/<catalyst_id>/compositions', methods=['POST'])
def add_composition():
    """Add a new composition to a catalyst"""
    data = request.get_json()
    catalyst_id = data.get('catalyst_id')
    composition = data.get('composition')
    percentage = data.get('percentage')
    provider = data.get('provider')
    
    if not all([catalyst_id, composition, percentage is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    try:
        percentage = float(percentage)
        if percentage <= 0 or percentage > 1:
            return jsonify({'status': 'error', 'message': 'Percentage must be between 0 and 1'}), 400
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Percentage must be a valid number'}), 400
    
    success, message = add_composition_service(catalyst_id, composition, percentage, provider)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@catalyst_composition_bp.route('/api/compositions/<composition_id>', methods=['PUT'])
def update_composition(composition_id):
    """Update an existing composition"""
    data = request.get_json()
    composition = data.get('composition')
    percentage = data.get('percentage')
    provider = data.get('provider')
    
    if not all([composition, percentage is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    try:
        percentage = float(percentage)
        if percentage <= 0 or percentage > 1:
            return jsonify({'status': 'error', 'message': 'Percentage must be between 0 and 1'}), 400
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Percentage must be a valid number'}), 400
    
    success, message = update_composition_service(composition_id, composition, percentage, provider)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@catalyst_composition_bp.route('/api/compositions/<composition_id>', methods=['DELETE'])
def delete_composition_route(composition_id):
    """Delete a composition"""
    success, message = delete_composition_service(composition_id)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 404
    
    return jsonify({
        'status': 'success',
        'message': message
    }) 