from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services.feed_service import (
    get_feeds_service, 
    get_feed_service, 
    add_feed_service, 
    update_feed_service, 
    delete_feed_service
)
from app.services.auth_service import login_required

feed_bp = Blueprint('feed', __name__, url_prefix='/feeds')

@feed_bp.route('/', methods=['GET'])
@login_required
def feeds_page():
    feeds = get_feeds_service()
    return render_template('feeds.html', feeds=feeds)

@feed_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_feed_page():
    if request.method == 'POST':
        feed_name = request.form.get('feed_name', '')
        provider = request.form.get('provider', '')
        
        success, message = add_feed_service(feed_name, provider)
        
        if success:
            flash('Feed added successfully!', 'success')
            return redirect(url_for('feed.feeds_page'))
        else:
            return render_template('add_feed.html', error=message, 
                                  feed_name=feed_name, 
                                  provider=provider)
    
    return render_template('add_feed.html')

@feed_bp.route('/edit/<feed_name>', methods=['GET', 'POST'])
@login_required
def edit_feed_page(feed_name):
    feed = get_feed_service(feed_name)
    if not feed:
        flash('Feed not found!', 'danger')
        return redirect(url_for('feed.feeds_page'))
    
    if request.method == 'POST':
        provider = request.form.get('provider', '')
        
        success, message = update_feed_service(feed_name, provider)
        
        if success:
            flash('Feed updated successfully!', 'success')
            return redirect(url_for('feed.feeds_page'))
        else:
            return render_template('edit_feed.html', feed=feed, error=message)
    
    return render_template('edit_feed.html', feed=feed)

@feed_bp.route('/delete/<feed_name>', methods=['POST'])
@login_required
def delete_feed_page(feed_name):
    result, message = delete_feed_service(feed_name)
    if result:
        flash('Feed deleted successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('feed.feeds_page')) 