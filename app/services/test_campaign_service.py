from app.repositories.test_campaign_repository import (
    get_all_test_campaigns,
    get_test_campaigns_paginated,
    get_test_campaign_by_id,
    add_test_campaign,
    update_test_campaign,
    delete_test_campaign,
    create_test_campaign_table,
    get_batch_id_exists
)
from app.repositories.operator_repository import get_operator_by_name
from app.repositories.reactor_repository import get_reactor_by_name
from app.repositories.feed_repository import get_feed_by_name
from app.repositories.catalyst_repository import get_catalyst_by_name
from app.repositories.project_repository import get_project_by_name

def get_test_campaigns_service():
    """
    Service function to get all test campaigns
    """
    return get_all_test_campaigns()

def get_test_campaigns_paginated_service(page=1, per_page=10, search_term=None):
    """
    Service function to get paginated test campaigns with optional search
    """
    return get_test_campaigns_paginated(page, per_page, search_term)

def get_test_campaign_service(test_campaign_id):
    """
    Service function to get a specific test campaign by id
    """
    return get_test_campaign_by_id(test_campaign_id)

def add_test_campaign_service(test_campaign_name, operator_name, reactor_name, feed_name, catalyst_name, project_name):
    """
    Service function to add a new test campaign.
    Translates names to IDs before calling the repository function.
    """
    # Get entity IDs from their names
    operator = get_operator_by_name(operator_name)
    if not operator:
        return False, f"Operator '{operator_name}' not found", None
    
    reactor = get_reactor_by_name(reactor_name)
    if not reactor:
        return False, f"Reactor '{reactor_name}' not found", None
    
    feed = get_feed_by_name(feed_name)
    if not feed:
        return False, f"Feed '{feed_name}' not found", None
    
    catalyst = get_catalyst_by_name(catalyst_name)
    if not catalyst:
        return False, f"Catalyst '{catalyst_name}' not found", None
    
    project = get_project_by_name(project_name)
    print(project, "project", flush=True)
    if not project:
        return False, f"Project '{project_name}' not found", None
    
    # Add the test campaign with entity IDs
    result = add_test_campaign(
        test_campaign_name,
        operator["operator_id"],
        reactor["reactor_id"],
        feed["feed_id"],
        catalyst["catalyst_id"],
        project["project_id"]
    )
    
    # Trả về kết quả với định dạng phù hợp
    if result[0]:  # Nếu thành công
        campaign_data = result[2]  # Lấy dict chứa test_campaign_id và batch_id
        return True, f"Test campaign created with Batch ID: {campaign_data['batch_id']}", campaign_data['test_campaign_id']
    else:
        return result  # Giữ nguyên kết quả lỗi

def update_test_campaign_service(test_campaign_id, test_campaign_name, operator_name, reactor_name, feed_name, catalyst_name, project_name):
    """
    Service function to update an existing test campaign.
    Translates names to IDs before calling the repository function.
    """
    # Get entity IDs from their names
    operator = get_operator_by_name(operator_name)
    if not operator:
        return False, f"Operator '{operator_name}' not found"
    
    reactor = get_reactor_by_name(reactor_name)
    if not reactor:
        return False, f"Reactor '{reactor_name}' not found"
    
    feed = get_feed_by_name(feed_name)
    if not feed:
        return False, f"Feed '{feed_name}' not found"
    
    catalyst = get_catalyst_by_name(catalyst_name)
    if not catalyst:
        return False, f"Catalyst '{catalyst_name}' not found"
    
    project = get_project_by_name(project_name)
    print(project, "project", flush=True)
    if not project:
        return False, f"Project '{project_name}' not found"
    
    # Update the test campaign with entity IDs
    return update_test_campaign(
        test_campaign_id,
        test_campaign_name,
        operator["operator_id"],
        reactor["reactor_id"],
        feed["feed_id"],
        catalyst["catalyst_id"],
        project["project_id"]
    )

def delete_test_campaign_service(test_campaign_id):
    """
    Service function to delete a test campaign
    """
    return delete_test_campaign(test_campaign_id)

def initialize_test_campaign_db():
    """
    Initialize the test campaign database table
    """
    print("🔧 Initializing test campaign database...")
    create_test_campaign_table()
    return True

def get_entity_suggestions(entity_type, search_term):
    """
    Get suggestions for entity names based on search term
    """
    if not search_term or len(search_term) < 2:
        return []
        
    search_term = search_term.lower()
    result = []
    limit = 10  # Limit to 10 suggestions
    
    try:
        if entity_type == 'operator':
            from app.repositories.operator_repository import get_all_operators
            operators = get_all_operators()
            result = [op["operator_name"] for op in operators if search_term in op["operator_name"].lower()]
            
        elif entity_type == 'reactor':
            from app.repositories.reactor_repository import get_all_reactors
            reactors = get_all_reactors()
            result = [r["reactor_name"] for r in reactors if search_term in r["reactor_name"].lower()]
            
        elif entity_type == 'feed':
            from app.repositories.feed_repository import get_all_feeds
            feeds = get_all_feeds()
            result = [f["feed_name"] for f in feeds if search_term in f["feed_name"].lower()]
            
        elif entity_type == 'catalyst':
            from app.repositories.catalyst_repository import get_all_catalysts
            catalysts = get_all_catalysts()
            result = [c["catalyst_name"] for c in catalysts if search_term in c["catalyst_name"].lower()]
            
        elif entity_type == 'project':
            from app.repositories.project_repository import get_all_projects
            projects = get_all_projects()
            result = [p["project_name"] for p in projects if search_term in p["project_name"].lower()]
        
        # Sort results by relevance (starts with search term first, then contains)
        starts_with = [item for item in result if item.lower().startswith(search_term)]
        contains = [item for item in result if not item.lower().startswith(search_term)]
        
        # Return sorted results with limit applied
        return (starts_with + contains)[:limit]
        
    except Exception as e:
        print(f"Error getting suggestions for {entity_type}: {str(e)}")
        return [] 
    

def check_batch_id_exists(batch_id):
    if get_batch_id_exists(batch_id):
        return True
    else:
        return False


