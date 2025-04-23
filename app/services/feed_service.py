from app.repositories.feed_repository import (
    get_all_feeds,
    get_feed_by_name,
    add_feed,
    update_feed,
    delete_feed,
    create_feed_table
)
from app.repositories.feed_composition_repository import get_total_percentage_for_feed

def get_feeds_service():
    """
    Service function to get all feeds
    """
    feeds = get_all_feeds()
    
    # Add composition percentage info to each feed
    for feed in feeds:
        feed["total_percentage"] = get_total_percentage_for_feed(feed["feed_id"])
        feed["is_complete"] = abs(feed["total_percentage"] - 1.0) < 0.0001  # Allow small floating point error
    
    return feeds

def get_feed_service(feed_name):
    """
    Service function to get a specific feed by name
    """
    feed = get_feed_by_name(feed_name)
    if feed:
        feed["total_percentage"] = get_total_percentage_for_feed(feed["feed_id"])
        feed["is_complete"] = abs(feed["total_percentage"] - 1.0) < 0.0001  # Allow small floating point error
    return feed

def add_feed_service(feed_name, provider):
    """
    Service function to add a new feed
    """
    return add_feed(feed_name, provider)

def update_feed_service(feed_name, provider):
    """
    Service function to update an existing feed
    """
    return update_feed(feed_name, provider)

def delete_feed_service(feed_name):
    """
    Service function to delete a feed
    """
    return delete_feed(feed_name)

def initialize_feed_db():
    """
    Initialize the feed database table
    """
    print("🔧 Initializing feed database...")
    create_feed_table()
    return True 