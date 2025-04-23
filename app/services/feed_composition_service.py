from app.repositories.feed_composition_repository import (
    get_compositions_by_feed_id,
    get_composition_by_id,
    add_composition,
    update_composition,
    delete_composition,
    get_feed_with_compositions,
    create_feed_composition_table,
    get_total_percentage_for_feed
)
from app.services.feed_service import get_feed_service

def get_compositions_service(feed_id):
    """
    Service function to get all compositions for a feed
    """
    return get_compositions_by_feed_id(feed_id)

def get_composition_service(composition_id):
    """
    Service function to get a specific composition by ID
    """
    return get_composition_by_id(composition_id)

def add_composition_service(feed_id, composition, percentage, provider):
    """
    Service function to add a new composition
    """
    return add_composition(feed_id, composition, percentage, provider)

def update_composition_service(composition_id, composition, percentage, provider):
    """
    Service function to update an existing composition
    """
    return update_composition(composition_id, composition, percentage, provider)

def delete_composition_service(composition_id):
    """
    Service function to delete a composition
    """
    return delete_composition(composition_id)

def get_feed_with_compositions_service(feed_id):
    """
    Service function to get a feed with all its compositions
    """
    return get_feed_with_compositions(feed_id)

def search_feeds_by_name_service(search_term):
    """
    Search feeds by name
    """
    from app.repositories.feed_repository import get_all_feeds
    feeds = get_all_feeds()
    if search_term:
        return [feed for feed in feeds if search_term.lower() in feed["feed_name"].lower()]
    return feeds

def get_remaining_percentage_service(feed_id):
    """
    Calculate the remaining percentage available for a feed
    """
    total = get_total_percentage_for_feed(feed_id)
    return 1.0 - total

def initialize_feed_composition_db():
    """
    Initialize the feed composition database table
    """
    print("🔧 Initializing feed composition database...")
    create_feed_composition_table()
    return True 