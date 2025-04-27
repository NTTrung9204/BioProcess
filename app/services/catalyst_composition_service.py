from app.repositories.catalyst_composition_repository import (
    get_compositions_by_catalyst_id,
    get_all_compositions,
    get_composition_by_id,
    get_relation_by_id,
    add_composition,
    update_composition,
    delete_composition,
    add_composition_to_catalyst,
    update_catalyst_composition,
    remove_composition_from_catalyst,
    get_catalyst_with_compositions,
    create_catalyst_composition_table,
    get_total_percentage_for_catalyst,
    search_compositions_by_name
)
from app.repositories.catalyst_repository import get_all_catalysts

def get_compositions_service(catalyst_id):
    """
    Service function to get all compositions for a catalyst
    """
    return get_compositions_by_catalyst_id(catalyst_id)

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
    Service function to get a specific catalyst-composition relationship by ID
    """
    return get_relation_by_id(relation_id)

def add_composition_service(name, quantity, surface_area=None, acidity=None, support_type=None, provider=None, impurity=0, proportion=0):
    """
    Service function to add a new composition
    """
    try:
        quantity = float(quantity)
    except (ValueError, TypeError):
        return False, "Quantity must be a valid number"
    
    if surface_area:
        try:
            surface_area = float(surface_area)
        except (ValueError, TypeError):
            return False, "Surface area must be a valid number"
    
    if acidity:
        try:
            acidity = float(acidity)
        except (ValueError, TypeError):
            return False, "Acidity must be a valid number"
    
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
    
    return add_composition(name, quantity, surface_area, acidity, support_type, provider, impurity, proportion)

def update_composition_service(composition_id, name, quantity, surface_area=None, acidity=None, support_type=None, provider=None, impurity=0, proportion=0):
    """
    Service function to update an existing composition
    """
    try:
        quantity = float(quantity)
    except (ValueError, TypeError):
        return False, "Quantity must be a valid number"
    
    if surface_area:
        try:
            surface_area = float(surface_area)
        except (ValueError, TypeError):
            return False, "Surface area must be a valid number"
    
    if acidity:
        try:
            acidity = float(acidity)
        except (ValueError, TypeError):
            return False, "Acidity must be a valid number"
    
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
    
    return update_composition(composition_id, name, quantity, surface_area, acidity, support_type, provider, impurity, proportion)

def delete_composition_service(composition_id):
    """
    Service function to delete a composition
    """
    return delete_composition(composition_id)

def add_composition_to_catalyst_service(catalyst_id, composition_id, percentage, quantity_used):
    """
    Service function to add a composition to a catalyst
    """
    try:
        percentage = float(percentage)
    except (ValueError, TypeError):
        return False, "Percentage must be a valid number"
    
    try:
        quantity_used = float(quantity_used)
    except (ValueError, TypeError):
        return False, "Quantity used must be a valid number"
    
    return add_composition_to_catalyst(catalyst_id, composition_id, percentage, quantity_used)

def update_catalyst_composition_service(relation_id, percentage, quantity_used):
    """
    Service function to update a catalyst-composition relationship
    """
    try:
        percentage = float(percentage)
    except (ValueError, TypeError):
        return False, "Percentage must be a valid number"
    
    try:
        quantity_used = float(quantity_used)
    except (ValueError, TypeError):
        return False, "Quantity used must be a valid number"
    
    return update_catalyst_composition(relation_id, percentage, quantity_used)

def remove_composition_from_catalyst_service(relation_id):
    """
    Service function to remove a composition from a catalyst
    """
    return remove_composition_from_catalyst(relation_id)

def get_catalyst_with_compositions_service(catalyst_id):
    """
    Service function to get a catalyst with all its compositions
    """
    return get_catalyst_with_compositions(catalyst_id)

def search_catalysts_by_name_service(search_term):
    """
    Search catalysts by name
    """
    from app.repositories.catalyst_repository import get_all_catalysts
    catalysts = get_all_catalysts()
    if search_term:
        return [catalyst for catalyst in catalysts if search_term.lower() in catalyst["catalyst_name"].lower()]
    return catalysts

def get_remaining_percentage_service(catalyst_id):
    """
    Calculate the remaining percentage available for a catalyst
    """
    total = get_total_percentage_for_catalyst(catalyst_id)
    return 1.0 - total

def initialize_catalyst_composition_db():
    """
    Initialize the database schema for the application
    """
    print("🔧 Initializing database schema for catalyst compositions...")
    return create_catalyst_composition_table()

def search_catalyst_compositions_by_name_service(search_term):
    """
    Service function to search compositions by name
    """
    return search_compositions_by_name(search_term)