from app.repositories.reactor_repository import (
    get_all_reactors,
    get_reactor_by_name,
    add_reactor,
    update_reactor,
    delete_reactor,
    create_reactor_table
)

def get_reactors_service():
    """
    Service function to get all reactors
    """
    return get_all_reactors()

def get_reactor_service(reactor_name):
    """
    Service function to get a specific reactor by name
    """
    return get_reactor_by_name(reactor_name)

def add_reactor_service(reactor_name, maintenance_day):
    """
    Service function to add a new reactor
    """
    return add_reactor(reactor_name, maintenance_day)

def update_reactor_service(reactor_name, maintenance_day):
    """
    Service function to update an existing reactor
    """
    return update_reactor(reactor_name, maintenance_day)

def delete_reactor_service(reactor_name):
    """
    Service function to delete a reactor
    """
    return delete_reactor(reactor_name)

def initialize_reactor_db():
    """
    Initialize the reactor database table
    """
    print("🔧 Initializing reactor database...")
    create_reactor_table()
    return True 