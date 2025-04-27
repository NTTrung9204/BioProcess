from app.repositories.feed_composition_repository import (
    get_compositions_by_feed_id,
    get_all_compositions,
    get_composition_by_id,
    get_relation_by_id,
    add_composition,
    update_composition,
    delete_composition,
    add_composition_to_feed,
    update_feed_composition,
    remove_composition_from_feed,
    get_feed_with_compositions,
    create_feed_composition_table,
    get_total_percentage_for_feed,
    search_compositions_by_name
)
from app.repositories.feed_repository import get_all_feeds

def get_compositions_service(feed_id):
    """
    Service function to get all compositions for a feed
    """
    return get_compositions_by_feed_id(feed_id)

def get_all_compositions_service():
    """
    Service function to get all compositions
    """
    return get_all_compositions()

def get_composition_service(composition_id):
    """
    Service function to get a specific composition by ID
    """
    return get_composition_by_id(composition_id)

def get_relation_service(relation_id):
    """
    Service function to get a specific feed-composition relationship by ID
    """
    return get_relation_by_id(relation_id)

def add_composition_service(name, quantity, viscosity=None, pH=None, density=None, water=None, provider=None, impurity=0, proportion=0):
    """
    Service function to add a new composition
    """
    try:
        quantity = float(quantity)
    except (ValueError, TypeError):
        return False, "Quantity must be a valid number"
    
    if viscosity:
        try:
            viscosity = float(viscosity)
        except (ValueError, TypeError):
            return False, "Viscosity must be a valid number"
    
    if pH:
        try:
            pH = float(pH)
        except (ValueError, TypeError):
            return False, "pH must be a valid number"
    
    try:
        impurity = float(impurity)
        if impurity < 0 or impurity > 1:
            return False, "Impurity must be between 0 and 1"
    except (ValueError, TypeError):
        return False, "Impurity must be a valid number"
        
    try:
        proportion = float(proportion)
        if proportion < 0 or proportion > 1:
            return False, "Proportion must be between 0 and 1"
    except (ValueError, TypeError):
        return False, "Proportion must be a valid number"
    
    return add_composition(name, quantity, viscosity, pH, density, water, provider, impurity, proportion)

def update_composition_service(composition_id, name, quantity, viscosity=None, pH=None, density=None, water=None, provider=None, impurity=0, proportion=0):
    """
    Service function to update an existing composition
    """
    try:
        quantity = float(quantity)
    except (ValueError, TypeError):
        return False, "Quantity must be a valid number"
    
    if viscosity:
        try:
            viscosity = float(viscosity)
        except (ValueError, TypeError):
            return False, "Viscosity must be a valid number"
    
    if pH:
        try:
            pH = float(pH)
        except (ValueError, TypeError):
            return False, "pH must be a valid number"
    
    try:
        impurity = float(impurity)
        if impurity < 0 or impurity > 1:
            return False, "Impurity must be between 0 and 1"
    except (ValueError, TypeError):
        return False, "Impurity must be a valid number"
        
    try:
        proportion = float(proportion)
        if proportion < 0 or proportion > 1:
            return False, "Proportion must be between 0 and 1"
    except (ValueError, TypeError):
        return False, "Proportion must be a valid number"
    
    return update_composition(composition_id, name, quantity, viscosity, pH, density, water, provider, impurity, proportion)

def delete_composition_service(composition_id):
    """
    Service function to delete a composition
    """
    return delete_composition(composition_id)

def add_composition_to_feed_service(feed_id, composition_id, percentage, quantity_used):
    """
    Service function to add a composition to a feed
    """
    try:
        percentage = float(percentage)
    except (ValueError, TypeError):
        return False, "Percentage must be a valid number"
    
    try:
        quantity_used = float(quantity_used)
    except (ValueError, TypeError):
        return False, "Quantity used must be a valid number"
    
    return add_composition_to_feed(feed_id, composition_id, percentage, quantity_used)

def update_feed_composition_service(relation_id, percentage, quantity_used):
    """
    Service function to update a feed-composition relationship
    """
    try:
        percentage = float(percentage)
    except (ValueError, TypeError):
        return False, "Percentage must be a valid number"
    
    try:
        quantity_used = float(quantity_used)
    except (ValueError, TypeError):
        return False, "Quantity used must be a valid number"
    
    return update_feed_composition(relation_id, percentage, quantity_used)

def remove_composition_from_feed_service(relation_id):
    """
    Service function to remove a composition from a feed
    """
    return remove_composition_from_feed(relation_id)

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
    Initialize the database schema for the application
    """
    print("🔧 Initializing database schema for feed compositions...")
    return create_feed_composition_table()

def search_feed_compositions_by_name_service(search_term):
    """
    Service function to search compositions by name
    """
    return search_compositions_by_name(search_term)