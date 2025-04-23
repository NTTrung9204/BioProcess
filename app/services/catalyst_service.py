from app.repositories.catalyst_composition_repository import get_total_percentage_for_catalyst
from app.repositories.catalyst_repository import (
    get_all_catalysts,
    get_catalyst_by_name,
    add_catalyst,
    update_catalyst,
    delete_catalyst,
    create_catalyst_table
)

def get_catalysts_service():
    """
    Service function to get all catalysts
    """

    catalysts = get_all_catalysts()

    for catalyst in catalysts:
        catalyst["total_percentage"] = get_total_percentage_for_catalyst(catalyst["catalyst_id"])
        catalyst["is_complete"] = abs(catalyst["total_percentage"] - 1.0) < 0.0001  # Allow small floating point error
    
    return catalysts

def get_catalyst_service(catalyst_name):
    """
    Service function to get a specific catalyst by name
    """
    return get_catalyst_by_name(catalyst_name)

def add_catalyst_service(catalyst_name, provider):
    """
    Service function to add a new catalyst
    """
    return add_catalyst(catalyst_name, provider)

def update_catalyst_service(catalyst_name, provider):
    """
    Service function to update an existing catalyst
    """
    return update_catalyst(catalyst_name, provider)

def delete_catalyst_service(catalyst_name):
    """
    Service function to delete a catalyst
    """
    return delete_catalyst(catalyst_name)

def initialize_catalyst_db():
    """
    Initialize the catalyst database table
    """
    print("🔧 Initializing catalyst database...")
    create_catalyst_table()
    return True 