from flask import Blueprint, request, jsonify, render_template, url_for, redirect, flash
import math
from app.services.auth_service import login_required
from app.services.test_campaign_service import (
    get_test_campaigns_service,
    get_test_campaigns_paginated_service,
    get_test_campaign_service,
    add_test_campaign_service,
    update_test_campaign_service,
    delete_test_campaign_service,
    get_entity_suggestions
)

test_campaign_bp = Blueprint('test_campaign', __name__, url_prefix='/test-campaign')

@test_campaign_bp.route('/', methods=['GET'])
@login_required
def list_test_campaigns():
    """
    Route to list all test campaigns with pagination
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_term = request.args.get('search', None)
    
    result = get_test_campaigns_paginated_service(page, per_page, search_term)
    
    if not result[1]:
        return render_template('test_campaigns.html', test_campaigns=[], pagination=None)
    
    test_campaigns, total_count = result[0], result[1]
    total_pages = math.ceil(total_count / per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_items': total_count,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'search_term': search_term
    }
    
    return render_template('test_campaigns.html', test_campaigns=test_campaigns, pagination=pagination)

@test_campaign_bp.route('/api/list', methods=['GET'])
@login_required
def api_list_test_campaigns():
    """
    API route to list all test campaigns
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', None)
    
    result = get_test_campaigns_paginated_service(page, per_page, search_term)
    
    if not result[0]:
        return jsonify({'success': False, 'message': result[1]}), 400
    
    test_campaigns, total_count = result[1], result[2]
    total_pages = math.ceil(total_count / per_page)
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_items': total_count,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }
    
    return jsonify({
        'success': True,
        'test_campaigns': test_campaigns,
        'pagination': pagination
    })

@test_campaign_bp.route('/new', methods=['GET'])
@login_required
def new_test_campaign_form():
    """
    Route to render the form for creating a new test campaign
    """
    return render_template('add_test_campaigns.html')

@test_campaign_bp.route('/<test_campaign_id>', methods=['GET'])
@login_required
def view_test_campaign(test_campaign_id):
    test_campaign = get_test_campaign_service(test_campaign_id)
    
    if not test_campaign:
        flash("Test campaign not found", 'danger')
        return redirect(url_for('test_campaign.list_test_campaigns'))
    
    return render_template('test_campaigns_detail.html', test_campaign=test_campaign)

@test_campaign_bp.route('/api/<test_campaign_id>', methods=['GET'])
@login_required
def api_get_test_campaign(test_campaign_id):
    """
    API route to get a single test campaign
    """
    # Chuyển đổi test_campaign_id thành số nguyên nếu có thể
    try:
        test_campaign_id = int(test_campaign_id)
    except ValueError:
        # Nếu không thể chuyển đổi (có thể là UUID string), để nguyên giá trị
        pass
        
    result = get_test_campaign_service(test_campaign_id)
    
    if not result[0]:
        return jsonify({'success': False, 'message': result[1]}), 404
    
    return jsonify({'success': True, 'test_campaign': result[1]})

@test_campaign_bp.route('/edit/<test_campaign_id>', methods=['GET'])
@login_required
def edit_test_campaign_form(test_campaign_id):
    test_campaign = get_test_campaign_service(test_campaign_id)
    
    if not test_campaign:
        flash("Test campaign not found", 'danger')
        return redirect(url_for('test_campaign.list_test_campaigns'))
    
    return render_template('edit_test_campaign.html', test_campaign=test_campaign)

@test_campaign_bp.route('/api/create', methods=['POST'])
@login_required
def api_create_test_campaign():
    """
    API route to create a new test campaign
    """
    data = request.json
    
    # Validate required fields
    required_fields = ['test_campaign_name', 'operator_name', 'reactor_name', 
                      'feed_name', 'catalyst_name', 'project_name']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    result = add_test_campaign_service(
        data['test_campaign_name'],
        data['operator_name'],
        data['reactor_name'],
        data['feed_name'],
        data['catalyst_name'],
        data['project_name']
    )
    
    if not result[0]:
        return jsonify({'success': False, 'message': result[1]}), 400
    
    # Phần success_message bây giờ sẽ chứa thông tin về Batch ID
    return jsonify({
        'success': True, 
        'message': result[1], 
        'test_campaign_id': result[2]
    })

@test_campaign_bp.route('/create', methods=['POST'])
@login_required
def create_test_campaign():
    """
    Route to create a new test campaign
    """
    # Validate required fields
    required_fields = ['test_campaign_name', 'operator_name', 'reactor_name', 
                      'feed_name', 'catalyst_name', 'project_name']
    
    for field in required_fields:
        if field not in request.form or not request.form[field]:
            flash(f'Missing required field: {field}', 'danger')
            return redirect(url_for('test_campaign.new_test_campaign_form'))
    
    result = add_test_campaign_service(
        request.form['test_campaign_name'],
        request.form['operator_name'],
        request.form['reactor_name'],
        request.form['feed_name'],
        request.form['catalyst_name'],
        request.form['project_name']
    )
    
    if not result[0]:
        flash(result[1], 'danger')
        return redirect(url_for('test_campaign.new_test_campaign_form'))
    
    # Hiển thị thông báo thành công với thông tin về Batch ID
    flash(result[1], 'success')
    # Chuyển hướng đến trang xem test campaign
    print(url_for('test_campaign.view_test_campaign', test_campaign_id=result[2]), flush=True)
    return redirect(url_for('test_campaign.view_test_campaign', test_campaign_id=result[2]))

@test_campaign_bp.route('/api/update/<test_campaign_id>', methods=['PUT'])
@login_required
def api_update_test_campaign(test_campaign_id):
    """
    API route to update a test campaign
    """
    data = request.json
    
    # Validate required fields
    required_fields = ['test_campaign_name', 'operator_name', 'reactor_name', 
                      'feed_name', 'catalyst_name', 'project_name']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    # Chuyển đổi test_campaign_id thành số nguyên nếu có thể
    try:
        test_campaign_id_int = int(test_campaign_id)
    except ValueError:
        # Nếu không thể chuyển đổi (có thể là UUID string), để nguyên giá trị
        test_campaign_id_int = test_campaign_id
    
    result = update_test_campaign_service(
        test_campaign_id_int,
        data['test_campaign_name'],
        data['operator_name'],
        data['reactor_name'],
        data['feed_name'],
        data['catalyst_name'],
        data['project_name']
    )
    
    if not result[0]:
        return jsonify({'success': False, 'message': result[1]}), 400
    
    # Phần success_message bây giờ sẽ chứa thông tin về Batch ID
    return jsonify({
        'success': True, 
        'message': result[1], 
        'test_campaign_id': test_campaign_id
    })

@test_campaign_bp.route('/update/<test_campaign_id>', methods=['POST'])
@login_required
def update_test_campaign(test_campaign_id):
    """
    Route to update a test campaign
    """
    # Validate required fields
    required_fields = ['test_campaign_name', 'operator_name', 'reactor_name', 
                      'feed_name', 'catalyst_name', 'project_name']
    
    for field in required_fields:
        if field not in request.form or not request.form[field]:
            flash(f'Missing required field: {field}', 'danger')
            return redirect(url_for('test_campaign.edit_test_campaign_form', test_campaign_id=test_campaign_id))
    
    # Chuyển đổi test_campaign_id thành số nguyên nếu có thể
    try:
        test_campaign_id_int = int(test_campaign_id)
    except ValueError:
        # Nếu không thể chuyển đổi (có thể là UUID string), để nguyên giá trị
        test_campaign_id_int = test_campaign_id
    
    result = update_test_campaign_service(
        test_campaign_id_int,
        request.form['test_campaign_name'],
        request.form['operator_name'],
        request.form['reactor_name'],
        request.form['feed_name'],
        request.form['catalyst_name'],
        request.form['project_name']
    )
    
    if not result[0]:
        flash(result[1], 'danger')
        return redirect(url_for('test_campaign.edit_test_campaign_form', test_campaign_id=test_campaign_id))
    
    flash('Test campaign updated successfully', 'success')
    return redirect(url_for('test_campaign.view_test_campaign', test_campaign_id=test_campaign_id))

@test_campaign_bp.route('/api/delete/<test_campaign_id>', methods=['DELETE'])
@login_required
def api_delete_test_campaign(test_campaign_id):
    """
    API route to delete a test campaign
    """
    # Chuyển đổi test_campaign_id thành số nguyên nếu có thể
    try:
        test_campaign_id_int = int(test_campaign_id)
    except ValueError:
        # Nếu không thể chuyển đổi (có thể là UUID string), để nguyên giá trị
        test_campaign_id_int = test_campaign_id
    
    result = delete_test_campaign_service(test_campaign_id_int)
    
    if not result[0]:
        return jsonify({'success': False, 'message': result[1]}), 400
    
    return jsonify({'success': True, 'message': 'Test campaign deleted successfully'})

@test_campaign_bp.route('/delete/<test_campaign_id>', methods=['POST'])
@login_required
def delete_test_campaign(test_campaign_id):
    """
    Route to delete a test campaign
    """
    # Chuyển đổi test_campaign_id thành số nguyên nếu có thể
    try:
        test_campaign_id_int = int(test_campaign_id)
    except ValueError:
        # Nếu không thể chuyển đổi (có thể là UUID string), để nguyên giá trị
        test_campaign_id_int = test_campaign_id
    
    result = delete_test_campaign_service(test_campaign_id_int)
    
    if not result[0]:
        flash(result[1], 'danger')
        return redirect(url_for('test_campaign.view_test_campaign', test_campaign_id=test_campaign_id))
    
    flash('Test campaign deleted successfully', 'success')
    return redirect(url_for('test_campaign.list_test_campaigns'))

@test_campaign_bp.route('/api/entity-suggestions/<entity_type>', methods=['GET'])
@login_required
def api_get_entity_suggestions(entity_type):
    """
    API route to get entity name suggestions based on search term
    """
    search_term = request.args.get('q', '')
    
    if not search_term or len(search_term) < 2:
        return jsonify({'success': True, 'suggestions': []})
    
    if entity_type not in ['operator', 'reactor', 'feed', 'catalyst', 'project']:
        return jsonify({'success': False, 'message': f'Invalid entity type: {entity_type}'}), 400
    
    try:
        suggestions = get_entity_suggestions(entity_type, search_term)
        
        # Format the response based on entity type
        formatted_suggestions = []
        if entity_type == 'operator':
            formatted_suggestions = [{"id": item, "text": item} for item in suggestions]
        elif entity_type == 'reactor':
            formatted_suggestions = [{"id": item, "text": item} for item in suggestions]
        elif entity_type == 'feed':
            formatted_suggestions = [{"id": item, "text": item} for item in suggestions]
        elif entity_type == 'catalyst':
            formatted_suggestions = [{"id": item, "text": item} for item in suggestions]
        elif entity_type == 'project':
            formatted_suggestions = [{"id": item, "text": item} for item in suggestions]
        
        return jsonify({
            'success': True, 
            'suggestions': formatted_suggestions
        })
    except Exception as e:
        print(f"Error fetching suggestions for {entity_type}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching suggestions: {str(e)}'}), 500 