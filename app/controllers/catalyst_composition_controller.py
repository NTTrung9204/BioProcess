from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.services.catalyst_composition_service import (
    get_compositions_service,
    get_all_compositions_service,
    get_composition_service,
    get_relation_service,
    add_composition_service,
    update_composition_service,
    delete_composition_service,
    add_composition_to_catalyst_service,
    update_catalyst_composition_service,
    remove_composition_from_catalyst_service,
    get_catalyst_with_compositions_service,
    get_remaining_percentage_service,
    search_catalysts_by_name_service
)
from app.services.catalyst_service import get_catalyst_service
from app.services.auth_service import login_required

catalyst_composition_bp = Blueprint('catalyst_composition', __name__, url_prefix='/catalyst-compositions')

# Compositions management routes
@catalyst_composition_bp.route('/compositions', methods=['GET'])
@login_required
def compositions_page():
    """Render the compositions management page"""
    compositions = get_all_compositions_service()
    return render_template('catalyst_compositions.html', compositions=compositions)

@catalyst_composition_bp.route('/composition/add', methods=['GET', 'POST'])
@login_required
def add_composition_page():
    """Add a new composition"""
    if request.method == 'POST':
        name = request.form.get('name', '')
        quantity = request.form.get('quantity', '')
        surface_area = request.form.get('surface_area', None)
        acidity = request.form.get('acidity', None)
        support_type = request.form.get('support_type', None)
        provider = request.form.get('provider', None)
        impurity = request.form.get('impurity', 0)
        proportion = request.form.get('proportion', 0)
        
        success, result = add_composition_service(name, quantity, surface_area, acidity, support_type, provider, impurity, proportion)
        
        if success:
            flash('Composition added successfully!', 'success')
            return redirect(url_for('catalyst_composition.compositions_page'))
        else:
            return render_template('add_catalyst_composition.html', 
                                  error=result, 
                                  name=name,
                                  quantity=quantity,
                                  surface_area=surface_area,
                                  acidity=acidity,
                                  support_type=support_type,
                                  provider=provider,
                                  impurity=impurity,
                                  proportion=proportion)
    
    return render_template('add_catalyst_composition.html')

@catalyst_composition_bp.route('/composition/edit/<composition_id>', methods=['GET', 'POST'])
@login_required
def edit_composition_page(composition_id):
    """Edit an existing composition"""
    composition = get_composition_service(composition_id)
    if not composition:
        flash('Composition not found!', 'danger')
        return redirect(url_for('catalyst_composition.compositions_page'))
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        quantity = request.form.get('quantity', '')
        surface_area = request.form.get('surface_area', None)
        acidity = request.form.get('acidity', None)
        support_type = request.form.get('support_type', None)
        provider = request.form.get('provider', None)
        impurity = request.form.get('impurity', 0)
        proportion = request.form.get('proportion', 0)
        
        success, message = update_composition_service(composition_id, name, quantity, surface_area, acidity, support_type, provider, impurity, proportion)
        
        if success:
            flash('Composition updated successfully!', 'success')
            return redirect(url_for('catalyst_composition.compositions_page'))
        else:
            return render_template('edit_catalyst_composition.html', 
                                  error=message, 
                                  composition=composition)
    
    return render_template('edit_catalyst_composition.html', composition=composition)

@catalyst_composition_bp.route('/composition/delete/<composition_id>', methods=['POST'])
@login_required
def delete_composition_page(composition_id):
    """Delete a composition"""
    success, message = delete_composition_service(composition_id)
    
    if success:
        flash('Composition deleted successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('catalyst_composition.compositions_page'))

# Catalyst-Composition relationship routes
@catalyst_composition_bp.route('/manage/<catalyst_id>', methods=['GET'])
@login_required
def manage_compositions_page(catalyst_id):
    """Render the catalyst composition management page"""
    print(catalyst_id, "catalyst_id", flush=True)
    catalyst_data = get_catalyst_with_compositions_service(catalyst_id)
    print(catalyst_data, "catalyst_data", flush=True)
    if not catalyst_data:
        flash('Catalyst not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    remaining_percentage = get_remaining_percentage_service(catalyst_id)
    
    return render_template('catalyst_catalyst_compositions.html', 
                          catalyst=catalyst_data, 
                          remaining_percentage=remaining_percentage)

@catalyst_composition_bp.route('/add-to-catalyst/<catalyst_id>', methods=['GET', 'POST'])
@login_required
def add_composition_to_catalyst_page(catalyst_id):
    """Add a composition to a catalyst"""
    catalyst_data = get_catalyst_with_compositions_service(catalyst_id)
    if not catalyst_data:
        flash('Catalyst not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    # Get all compositions for selection
    compositions = get_all_compositions_service()
    
    if request.method == 'POST':
        composition_id = request.form.get('composition_id', '')
        percentage = request.form.get('percentage', '')
        quantity_used = request.form.get('quantity_used', '')
        
        success, message = add_composition_to_catalyst_service(catalyst_id, composition_id, percentage, quantity_used)
        
        if success:
            flash('Composition added to catalyst successfully!', 'success')
            return redirect(url_for('catalyst_composition.manage_compositions_page', catalyst_id=catalyst_id))
        else:
            return render_template('add_catalyst_catalyst_composition.html', 
                                  error=message, 
                                  catalyst=catalyst_data,
                                  compositions=compositions,
                                  composition_id=composition_id,
                                  percentage=percentage,
                                  quantity_used=quantity_used,
                                  remaining_percentage=get_remaining_percentage_service(catalyst_id))
    
    return render_template('add_catalyst_catalyst_composition.html', 
                          catalyst=catalyst_data,
                          compositions=compositions,
                          remaining_percentage=get_remaining_percentage_service(catalyst_id))

@catalyst_composition_bp.route('/edit-relation/<relation_id>', methods=['GET', 'POST'])
@login_required
def edit_catalyst_composition_page(relation_id):
    """Edit a catalyst-composition relationship"""
    relation = get_relation_service(relation_id)
    if not relation:
        flash('Relationship not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    catalyst_data = get_catalyst_with_compositions_service(relation['catalyst_id'])
    
    if request.method == 'POST':
        percentage = request.form.get('percentage', '')
        quantity_used = request.form.get('quantity_used', '')
        
        success, message = update_catalyst_composition_service(relation_id, percentage, quantity_used)
        
        if success:
            flash('Catalyst composition updated successfully!', 'success')
            return redirect(url_for('catalyst_composition.manage_compositions_page', catalyst_id=relation['catalyst_id']))
        else:
            return render_template('edit_catalyst_catalyst_composition.html', 
                                  error=message, 
                                  catalyst=catalyst_data,
                                  relation=relation,
                                  remaining_percentage=get_remaining_percentage_service(relation['catalyst_id']))
    
    return render_template('edit_catalyst_catalyst_composition.html', 
                          catalyst=catalyst_data,
                          relation=relation,
                          remaining_percentage=get_remaining_percentage_service(relation['catalyst_id']))

@catalyst_composition_bp.route('/remove-composition/<relation_id>', methods=['POST'])
@login_required
def remove_composition_from_catalyst_page(relation_id):
    """Remove a composition from a catalyst"""
    relation = get_relation_service(relation_id)
    if not relation:
        flash('Relationship not found!', 'danger')
        return redirect(url_for('catalyst.catalysts_page'))
    
    catalyst_id = relation['catalyst_id']
    
    success, message = remove_composition_from_catalyst_service(relation_id)
    
    if success:
        flash('Composition removed from catalyst successfully!', 'success')
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
@catalyst_composition_bp.route('/api/compositions', methods=['GET'])
@login_required
def get_all_compositions_api():
    """Get all compositions"""
    compositions = get_all_compositions_service()
    return jsonify({
        'status': 'success',
        'data': compositions
    })

@catalyst_composition_bp.route('/api/compositions/<composition_id>', methods=['GET'])
@login_required
def get_composition_api(composition_id):
    """Get a specific composition by ID"""
    composition = get_composition_service(composition_id)
    if not composition:
        return jsonify({'status': 'error', 'message': f'Composition with ID {composition_id} not found'}), 404
    
    return jsonify({
        'status': 'success',
        'data': composition
    })

@catalyst_composition_bp.route('/api/catalyst/<catalyst_id>/compositions', methods=['GET'])
@login_required
def get_catalyst_compositions_api(catalyst_id):
    """Get all compositions for a specific catalyst"""
    compositions = get_compositions_service(catalyst_id)
    return jsonify({
        'status': 'success',
        'data': compositions,
        'remaining_percentage': get_remaining_percentage_service(catalyst_id)
    })

@catalyst_composition_bp.route('/api/catalyst/<catalyst_id>/full', methods=['GET'])
@login_required
def get_catalyst_with_compositions_api(catalyst_id):
    """Get catalyst details with all its compositions"""
    result = get_catalyst_with_compositions_service(catalyst_id)
    if not result:
        return jsonify({'status': 'error', 'message': f'Catalyst with ID {catalyst_id} not found'}), 404
    
    return jsonify({
        'status': 'success',
        'data': result
    })

@catalyst_composition_bp.route('/api/compositions', methods=['POST'])
@login_required
def add_composition_api():
    """Add a new composition"""
    data = request.get_json()
    name = data.get('name')
    quantity = data.get('quantity')
    surface_area = data.get('surface_area')
    acidity = data.get('acidity')
    support_type = data.get('support_type')
    provider = data.get('provider')
    impurity = data.get('impurity', 0)
    proportion = data.get('proportion', 0)
    
    if not all([name, quantity is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    success, result = add_composition_service(name, quantity, surface_area, acidity, support_type, provider, impurity, proportion)
    
    if not success:
        return jsonify({'status': 'error', 'message': result}), 400
    
    return jsonify({
        'status': 'success',
        'message': 'Composition added successfully',
        'id': result
    })

@catalyst_composition_bp.route('/api/compositions/<composition_id>', methods=['PUT'])
@login_required
def update_composition_api(composition_id):
    """Update an existing composition"""
    data = request.get_json()
    name = data.get('name')
    quantity = data.get('quantity')
    surface_area = data.get('surface_area')
    acidity = data.get('acidity')
    support_type = data.get('support_type')
    provider = data.get('provider')
    impurity = data.get('impurity', 0)
    proportion = data.get('proportion', 0)
    
    if not all([name, quantity is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    success, message = update_composition_service(composition_id, name, quantity, surface_area, acidity, support_type, provider, impurity, proportion)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@catalyst_composition_bp.route('/api/compositions/<composition_id>', methods=['DELETE'])
@login_required
def delete_composition_api(composition_id):
    """Delete a composition"""
    success, message = delete_composition_service(composition_id)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@catalyst_composition_bp.route('/api/catalyst/<catalyst_id>/compositions', methods=['POST'])
@login_required
def add_composition_to_catalyst_api():
    """Add a composition to a catalyst"""
    data = request.get_json()
    catalyst_id = data.get('catalyst_id')
    composition_id = data.get('composition_id')
    percentage = data.get('percentage')
    quantity_used = data.get('quantity_used')
    
    if not all([catalyst_id, composition_id, percentage is not None, quantity_used is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    success, message = add_composition_to_catalyst_service(catalyst_id, composition_id, percentage, quantity_used)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@catalyst_composition_bp.route('/api/catalyst-compositions/<relation_id>', methods=['PUT'])
@login_required
def update_catalyst_composition_api(relation_id):
    """Update a catalyst-composition relationship"""
    data = request.get_json()
    percentage = data.get('percentage')
    quantity_used = data.get('quantity_used')
    
    if not all([percentage is not None, quantity_used is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    success, message = update_catalyst_composition_service(relation_id, percentage, quantity_used)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@catalyst_composition_bp.route('/api/catalyst-compositions/<relation_id>', methods=['DELETE'])
@login_required
def remove_composition_from_catalyst_api(relation_id):
    """Remove a composition from a catalyst"""
    success, message = remove_composition_from_catalyst_service(relation_id)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    }) 