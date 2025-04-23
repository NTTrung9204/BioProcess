from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.services.feed_composition_service import (
    get_compositions_service,
    get_composition_service,
    add_composition_service,
    update_composition_service,
    delete_composition_service,
    get_feed_with_compositions_service,
    get_remaining_percentage_service,
    search_feeds_by_name_service
)
from app.services.feed_service import get_feed_service
from app.services.auth_service import login_required

feed_composition_bp = Blueprint('feed_composition', __name__, url_prefix='/feed-compositions')

# Web routes with UI
@feed_composition_bp.route('/manage/<feed_id>', methods=['GET'])
@login_required
def manage_compositions_page(feed_id):
    """Render the feed composition management page"""
    feed_data = get_feed_with_compositions_service(feed_id)
    if not feed_data:
        flash('Feed not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    remaining_percentage = get_remaining_percentage_service(feed_id)
    
    return render_template('feed_compositions.html', 
                          feed=feed_data, 
                          remaining_percentage=remaining_percentage)

@feed_composition_bp.route('/add/<feed_id>', methods=['GET', 'POST'])
@login_required
def add_composition_page(feed_id):
    """Add a new composition to a feed"""
    feed_data = get_feed_with_compositions_service(feed_id)
    if not feed_data:
        flash('Feed not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    if request.method == 'POST':
        composition = request.form.get('composition', '')
        percentage = request.form.get('percentage', '')
        provider = request.form.get('provider', '')
        
        success, message = add_composition_service(feed_id, composition, percentage, provider)
        
        if success:
            flash('Composition added successfully!', 'success')
            return redirect(url_for('feed_composition.manage_compositions_page', feed_id=feed_id))
        else:
            return render_template('add_feed_composition.html', 
                                  error=message, 
                                  feed=feed_data,
                                  composition=composition,
                                  percentage=percentage,
                                  provider=provider,
                                  remaining_percentage=get_remaining_percentage_service(feed_id))
    
    return render_template('add_feed_composition.html', 
                          feed=feed_data,
                          remaining_percentage=get_remaining_percentage_service(feed_id))

@feed_composition_bp.route('/edit/<composition_id>', methods=['GET', 'POST'])
@login_required
def edit_composition_page(composition_id):
    """Edit an existing feed composition"""
    composition = get_composition_service(composition_id)
    if not composition:
        flash('Composition not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    feed_data = get_feed_with_compositions_service(composition['feed_id'])
    
    if request.method == 'POST':
        composition_name = request.form.get('composition', '')
        percentage = request.form.get('percentage', '')
        provider = request.form.get('provider', '')
        
        success, message = update_composition_service(composition_id, composition_name, percentage, provider)
        
        if success:
            flash('Composition updated successfully!', 'success')
            return redirect(url_for('feed_composition.manage_compositions_page', feed_id=composition['feed_id']))
        else:
            return render_template('edit_feed_composition.html', 
                                  error=message, 
                                  feed=feed_data,
                                  composition=composition,
                                  remaining_percentage=get_remaining_percentage_service(composition['feed_id']))
    
    return render_template('edit_feed_composition.html', 
                          feed=feed_data,
                          composition=composition,
                          remaining_percentage=get_remaining_percentage_service(composition['feed_id']))

@feed_composition_bp.route('/delete/<composition_id>', methods=['POST'])
@login_required
def delete_composition_page(composition_id):
    """Delete a feed composition"""
    composition = get_composition_service(composition_id)
    if not composition:
        flash('Composition not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    feed_id = composition['feed_id']
    
    success, message = delete_composition_service(composition_id)
    
    if success:
        flash('Composition deleted successfully!', 'success')
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
@feed_composition_bp.route('/api/feed/<feed_id>/compositions', methods=['GET'])
def get_feed_compositions(feed_id):
    """Get all compositions for a specific feed"""
    compositions = get_compositions_service(feed_id)
    return jsonify({
        'status': 'success',
        'data': compositions,
        'remaining_percentage': get_remaining_percentage_service(feed_id)
    })

@feed_composition_bp.route('/api/feed/<feed_id>/compositions/full', methods=['GET'])
def get_feed_with_compositions(feed_id):
    """Get feed details with all its compositions"""
    result = get_feed_with_compositions_service(feed_id)
    if not result:
        return jsonify({'status': 'error', 'message': f'Feed with ID {feed_id} not found'}), 404
    
    return jsonify({
        'status': 'success',
        'data': result
    })

@feed_composition_bp.route('/api/compositions/<composition_id>', methods=['GET'])
def get_composition(composition_id):
    """Get a specific composition by ID"""
    composition = get_composition_service(composition_id)
    if not composition:
        return jsonify({'status': 'error', 'message': f'Composition with ID {composition_id} not found'}), 404
    
    return jsonify({
        'status': 'success',
        'data': composition
    })

@feed_composition_bp.route('/api/feed/<feed_id>/compositions', methods=['POST'])
def add_composition():
    """Add a new composition to a feed"""
    data = request.get_json()
    feed_id = data.get('feed_id')
    composition = data.get('composition')
    percentage = data.get('percentage')
    provider = data.get('provider')
    
    if not all([feed_id, composition, percentage is not None]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    try:
        percentage = float(percentage)
        if percentage <= 0 or percentage > 1:
            return jsonify({'status': 'error', 'message': 'Percentage must be between 0 and 1'}), 400
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Percentage must be a valid number'}), 400
    
    success, message = add_composition_service(feed_id, composition, percentage, provider)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 400
    
    return jsonify({
        'status': 'success',
        'message': message
    })

@feed_composition_bp.route('/api/compositions/<composition_id>', methods=['PUT'])
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

@feed_composition_bp.route('/api/compositions/<composition_id>', methods=['DELETE'])
def delete_composition_route(composition_id):
    """Delete a composition"""
    success, message = delete_composition_service(composition_id)
    
    if not success:
        return jsonify({'status': 'error', 'message': message}), 404
    
    return jsonify({
        'status': 'success',
        'message': message
    }) 