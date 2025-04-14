from app.repositories import (
    create_project_table, get_all_projects, get_project_by_id, 
    add_project, update_project, delete_project
)

def initialize_project_db():
    return create_project_table()

def get_projects_service():
    return get_all_projects()

def get_project_service(project_id):
    return get_project_by_id(project_id)

def add_project_service(project_name, budget, project_manager, cust_name):
    if not project_name or len(project_name.strip()) < 6 or len(project_name.strip()) > 18:
        return False, "Project name must be between 6-18 characters"
    
    if not project_manager or len(project_manager.strip()) < 6 or len(project_manager.strip()) > 18:
        return False, "Project manager name must be between 6-18 characters"
    
    try:
        budget_value = float(budget) if budget else 0
    except ValueError:
        return False, "Budget must be a valid number"
    
    return add_project(project_name.strip(), budget_value, project_manager.strip(), cust_name)

def update_project_service(project_id, project_name, budget, project_manager, cust_name):
    project = get_project_by_id(project_id)
    if not project:
        return False, "Project not found"
    
    if not project_name or len(project_name.strip()) < 6 or len(project_name.strip()) > 18:
        return False, "Project name must be between 6-18 characters"
    
    if not project_manager or len(project_manager.strip()) < 6 or len(project_manager.strip()) > 18:
        return False, "Project manager name must be between 6-18 characters"
    
    try:
        budget_value = float(budget) if budget else 0
    except ValueError:
        return False, "Budget must be a valid number"
    
    return update_project(project_id, project_name.strip(), budget_value, project_manager.strip(), cust_name)

def delete_project_service(project_id):
    return delete_project(project_id) 