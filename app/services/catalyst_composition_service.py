from app.repositories.catalyst_composition_repository import (
    get_compositions_by_catalyst_id,
    get_composition_by_id,
    add_composition,
    update_composition,
    delete_composition,
    get_catalyst_with_compositions,
    create_catalyst_composition_table,
    get_total_percentage_for_catalyst
)
from app.repositories.catalyst_repository import get_all_catalysts

def get_compositions_service(catalyst_id):
    """
    Service function to get all compositions for a catalyst
    """
    return get_compositions_by_catalyst_id(catalyst_id)

def get_composition_service(composition_id):
    """
    Service function to get a specific composition by ID
    """
    return get_composition_by_id(composition_id)

def add_composition_service(catalyst_id, composition, percentage, provider):
    """
    Service function to add a new composition
    """
    return add_composition(catalyst_id, composition, percentage, provider)

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
    Initialize the catalyst composition database table
    """
    print("🔧 Initializing catalyst composition database...")
    create_catalyst_composition_table()
    return True