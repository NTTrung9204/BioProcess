from app.repositories.operator_repository import (
    get_all_operators,
    get_operator_by_name,
    add_operator,
    update_operator,
    delete_operator,
    create_operator_table
)

def get_operators_service():
    """
    Service function to get all operators
    """
    return get_all_operators()

def get_operator_service(operator_name):
    """
    Service function to get a specific operator by name
    """
    return get_operator_by_name(operator_name)

def add_operator_service(operator_name, level):
    """
    Service function to add a new operator
    """
    return add_operator(operator_name, level)

def update_operator_service(operator_name, level):
    """
    Service function to update an existing operator
    """
    return update_operator(operator_name, level)

def delete_operator_service(operator_name):
    """
    Service function to delete an operator
    """
    return delete_operator(operator_name)

def initialize_operator_db():
    """
    Initialize the operator database table
    """
    print("🔧 Initializing operator database...")
    create_operator_table()
    return True 