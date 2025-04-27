from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.services.feed_composition_service import (
    get_compositions_service,
    get_all_compositions_service,
    get_composition_service,
    get_relation_service,
    add_composition_service,
    update_composition_service,
    delete_composition_service,
    add_composition_to_feed_service,
    update_feed_composition_service,
    remove_composition_from_feed_service,
    get_feed_with_compositions_service,
    get_remaining_percentage_service,
    search_feeds_by_name_service
)
from app.services.feed_service import get_feed_service
from app.services.auth_service import login_required

feed_composition_bp = Blueprint('feed_composition', __name__, url_prefix='/feed-compositions')

# Compositions management routes
@feed_composition_bp.route('/compositions', methods=['GET'])
@login_required
def compositions_page():
    """Render the compositions management page"""
    compositions = get_all_compositions_service()
    return render_template('feed_compositions.html', compositions=compositions)

@feed_composition_bp.route('/composition/add', methods=['GET', 'POST'])
@login_required
def add_composition_page():
    """Add a new composition"""
    if request.method == 'POST':
        name = request.form.get('name', '')
        quantity = request.form.get('quantity', '')
        viscosity = request.form.get('viscosity', None)
        pH = request.form.get('pH', None)
        density = request.form.get('density', None)
        water = request.form.get('water', None)
        provider = request.form.get('provider', None)
        impurity = request.form.get('impurity', 0)
        proportion = request.form.get('proportion', 0)
        
        success, result = add_composition_service(name, quantity, viscosity, pH, density, water, provider, impurity, proportion)
        
        if success:
            flash('Composition added successfully!', 'success')
            return redirect(url_for('feed_composition.compositions_page'))
        else:
            return render_template('add_feed_composition.html', 
                                  error=result, 
                                  name=name,
                                  quantity=quantity,
                                  viscosity=viscosity,
                                  pH=pH,
                                  density=density,
                                  water=water,
                                  provider=provider,
                                  impurity=impurity,
                                  proportion=proportion)
    
    return render_template('add_feed_composition.html')

@feed_composition_bp.route('/composition/edit/<composition_id>', methods=['GET', 'POST'])
@login_required
def edit_composition_page(composition_id):
    """Edit an existing composition"""
    composition = get_composition_service(composition_id)
    if not composition:
        flash('Composition not found!', 'danger')
        return redirect(url_for('feed_composition.compositions_page'))
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        quantity = request.form.get('quantity', '')
        viscosity = request.form.get('viscosity', None)
        pH = request.form.get('pH', None)
        density = request.form.get('density', None)
        water = request.form.get('water', None)
        provider = request.form.get('provider', None)
        impurity = request.form.get('impurity', 0)
        proportion = request.form.get('proportion', 0)
        
        success, message = update_composition_service(composition_id, name, quantity, viscosity, pH, density, water, provider, impurity, proportion)
        
        if success:
            flash('Composition updated successfully!', 'success')
            return redirect(url_for('feed_composition.compositions_page'))
        else:
            return render_template('edit_feed_composition.html', 
                                  error=message, 
                                  composition=composition)
    
    return render_template('edit_feed_composition.html', composition=composition)

@feed_composition_bp.route('/composition/delete/<composition_id>', methods=['POST'])
@login_required
def delete_composition_page(composition_id):
    """Delete a composition"""
    success, message = delete_composition_service(composition_id)
    
    if success:
        flash('Composition deleted successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('feed_composition.compositions_page'))

# feed-Composition relationship routes
@feed_composition_bp.route('/manage/<feed_id>', methods=['GET'])
@login_required
def manage_compositions_page(feed_id):
    """Render the feed composition management page"""
    print(feed_id, "feed_id", flush=True)
    feed_data = get_feed_with_compositions_service(feed_id)
    print(feed_data, "feed_data", flush=True)
    if not feed_data:
        flash('feed not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    remaining_percentage = get_remaining_percentage_service(feed_id)
    
    return render_template('feed_feed_compositions.html', 
                          feed=feed_data, 
                          remaining_percentage=remaining_percentage)

@feed_composition_bp.route('/add-to-feed/<feed_id>', methods=['GET', 'POST'])
@login_required
def add_composition_to_feed_page(feed_id):
    """Add a composition to a feed"""
    feed_data = get_feed_with_compositions_service(feed_id)
    if not feed_data:
        flash('feed not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    # Get all compositions for selection
    compositions = get_all_compositions_service()
    
    if request.method == 'POST':
        composition_id = request.form.get('composition_id', '')
        percentage = request.form.get('percentage', '')
        quantity_used = request.form.get('quantity_used', '')
        
        success, message = add_composition_to_feed_service(feed_id, composition_id, percentage, quantity_used)
        
        if success:
            flash('Composition added to feed successfully!', 'success')
            return redirect(url_for('feed_composition.manage_compositions_page', feed_id=feed_id))
        else:
            return render_template('add_feed_feed_composition.html', 
                                  error=message, 
                                  feed=feed_data,
                                  compositions=compositions,
                                  composition_id=composition_id,
                                  percentage=percentage,
                                  quantity_used=quantity_used,
                                  remaining_percentage=get_remaining_percentage_service(feed_id))
    
    return render_template('add_feed_feed_composition.html', 
                          feed=feed_data,
                          compositions=compositions,
                          remaining_percentage=get_remaining_percentage_service(feed_id))

@feed_composition_bp.route('/edit-relation/<relation_id>', methods=['GET', 'POST'])
@login_required
def edit_feed_composition_page(relation_id):
    """Edit a feed-composition relationship"""
    relation = get_relation_service(relation_id)
    if not relation:
        flash('Relationship not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    feed_data = get_feed_with_compositions_service(relation['feed_id'])
    
    if request.method == 'POST':
        percentage = request.form.get('percentage', '')
        quantity_used = request.form.get('quantity_used', '')
        
        success, message = update_feed_composition_service(relation_id, percentage, quantity_used)
        
        if success:
            flash('feed composition updated successfully!', 'success')
            return redirect(url_for('feed_composition.manage_compositions_page', feed_id=relation['feed_id']))
        else:
            return render_template('edit_feed_feed_composition.html', 
                                  error=message, 
                                  feed=feed_data,
                                  relation=relation,
                                  remaining_percentage=get_remaining_percentage_service(relation['feed_id']))
    
    return render_template('edit_feed_feed_composition.html', 
                          feed=feed_data,
                          relation=relation,
                          remaining_percentage=get_remaining_percentage_service(relation['feed_id']))

@feed_composition_bp.route('/remove-composition/<relation_id>', methods=['POST'])
@login_required
def remove_composition_from_feed_page(relation_id):
    """Remove a composition from a feed"""
    relation = get_relation_service(relation_id)
    if not relation:
        flash('Relationship not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    feed_id = relation['feed_id']
    
    success, message = remove_composition_from_feed_service(relation_id)
    
    if success:
        flash('Composition removed from feed successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('feed_composition.manage_compositions_page', feed_id=feed_id))

@feed_composition_bp.route('/search-feeds', methods=['GET'])
@login_required
def search_feeds():
    """Search for feeds by name"""
    search_term = request.args.get('term', '')
    feeds = search_feeds_by_name_service(search_term)
    return jsonify(feeds)

# API routes
@feed_composition_bp.route('/api/compositions', methods=['GET'])
@login_required
def get_all_compositions_api():
    """Get all compositions"""
    compositions = get_all_compositions_service()
    return jsonify({
        'status': 'success',
        'data': compositions
    })

@feed_composition_bp.route('/api/compositions/<composition_id>', methods=['GET'])
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

@feed_composition_bp.route('/api/feed/<feed_id>/compositions', methods=['GET'])
@login_required
def get_feed_compositions_api(feed_id):
    """Get all compositions for a specific feed"""
    compositions = get_compositions_service(feed_id)
    return jsonify({
        'status': 'success',
        'data': compositions,
        'remaining_percentage': get_remaining_percentage_service(feed_id)
    })

@feed_composition_bp.route('/api/feed/<feed_id>/full', methods=['GET'])
@login_required
def get_feed_with_compositions_api(feed_id):
    """Get feed details with all its compositions"""
    result = get_feed_with_compositions_service(feed_id)
    if not result:
        return jsonify({'status': 'error', 'message': f'feed with ID {feed_id} not found'}), 404
    
    return jsonify({
        'status': 'success',
        'data': result
    })

@feed_composition_bp.route('/api/compositions', methods=['POST'])
@login_required
def add_composition_api():
    """Add a new composition"""
    data = request.get_json()
    name = data.get('name')
    quantity = data.get('quantity')
    viscosity = data.get('viscosity')
    pH = data.get('pH')
    density = data.get('density')
    water = data.get('water')
    provider = data.get('provider')
    impurity = data.get('impurity', 0)
    proportion = data.get('proportion', 0)
    
    if not all([name, quantity is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    success, result = add_composition_service(name, quantity, viscosity, pH, density, water, provider, impurity, proportion)
    
    if not success:
        return jsonify({'status': 'error', 'message': result}), 400
    
    return jsonify({
        'status': 'success',
        'message': 'Composition added successfully',
        'id': result
    })

@feed_composition_bp.route('/api/compositions/<composition_id>', methods=['PUT'])
@login_required
def update_composition_api(composition_id):
    """Update an existing composition"""
    data = request.get_json()
    name = data.get('name')
    quantity = data.get('quantity')
    viscosity = data.get('viscosity')
    pH = data.get('pH')
    density = data.get('density')
    water = data.get('water')
    provider = data.get('provider')
    impurity = data.get('impurity', 0)
    proportion = data.get('proportion', 0)
    
    if not all([name, quantity is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    success, message = update_composition_service(composition_id, name, quantity, viscosity, pH, density, water, provider, impurity, proportion)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@feed_composition_bp.route('/api/compositions/<composition_id>', methods=['DELETE'])
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

@feed_composition_bp.route('/api/feed/<feed_id>/compositions', methods=['POST'])
@login_required
def add_composition_to_feed_api():
    """Add a composition to a feed"""
    data = request.get_json()
    feed_id = data.get('feed_id')
    composition_id = data.get('composition_id')
    percentage = data.get('percentage')
    quantity_used = data.get('quantity_used')
    
    if not all([feed_id, composition_id, percentage is not None, quantity_used is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    success, message = add_composition_to_feed_service(feed_id, composition_id, percentage, quantity_used)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@feed_composition_bp.route('/api/feed-compositions/<relation_id>', methods=['PUT'])
@login_required
def update_feed_composition_api(relation_id):
    """Update a feed-composition relationship"""
    data = request.get_json()
    percentage = data.get('percentage')
    quantity_used = data.get('quantity_used')
    
    if not all([percentage is not None, quantity_used is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    success, message = update_feed_composition_service(relation_id, percentage, quantity_used)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@feed_composition_bp.route('/api/feed-compositions/<relation_id>', methods=['DELETE'])
@login_required
def remove_composition_from_feed_api(relation_id):
    """Remove a composition from a feed"""
    success, message = remove_composition_from_feed_service(relation_id)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    }) 