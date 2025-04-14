from app.repositories.database import get_db_connection
from app.config import PostgresConfig
import uuid

def create_project_table():
    """
    Create the project table in the database
    """
    print("🔧 Creating project table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS project (
                    project_id UUID DEFAULT gen_random_uuid() UNIQUE,
                    project_name VARCHAR(18) PRIMARY KEY CHECK (LENGTH(project_name) >= 6 AND LENGTH(project_name) <= 18),
                    budget NUMERIC(15, 2),
                    project_manager VARCHAR(18) CHECK (LENGTH(project_manager) >= 6 AND LENGTH(project_manager) <= 18),
                    cust_name VARCHAR(18) REFERENCES customer(cust_name) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table project created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating project table: {e}")
        return False
    finally:
        conn.close()

def get_all_projects():
    """
    Get all projects from the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.project_id, p.project_name, p.budget, p.project_manager, p.cust_name, p.created_at, c.contact_infor 
                FROM project p
                LEFT JOIN customer c ON p.cust_name = c.cust_name
                ORDER BY p.project_name
            """)
            projects = cur.fetchall()
            
            result = []
            for project in projects:
                result.append({
                    "project_id": project[0],
                    "project_name": project[1],
                    "budget": project[2],
                    "project_manager": project[3],
                    "cust_name": project[4],
                    "created_at": project[5],
                    "customer_contact": project[6]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting projects: {e}")
        return []
    finally:
        conn.close()

def get_project_by_id(proj_id):
    """
    Get project by ID
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT project_id, project_name, budget, project_manager, cust_name
                FROM project
                WHERE project_id = %s
            """, (proj_id,))
            project = cur.fetchone()
            if project is None:
                return None
            
            # Convert to dict
            project_dict = {
                'project_id': project[0],
                'project_name': project[1],
                'budget': project[2],
                'project_manager': project[3],
                'cust_name': project[4]
            }
            return project_dict
    except Exception as e:
        print(f"❌ Error getting project by ID: {e}")
        return None
    finally:
        conn.close()

def get_project_by_name(proj_name):
    """
    Get project by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT project_id, project_name, budget, project_manager, cust_name
                FROM project
                WHERE project_name = %s
            """, (proj_name,))
            project = cur.fetchone()
            if project is None:
                return None
            
            # Convert to dict
            project_dict = {
                'project_id': project[0],
                'project_name': project[1],
                'budget': project[2],
                'project_manager': project[3],
                'cust_name': project[4]
            }
            return project_dict
    except Exception as e:
        print(f"❌ Error getting project by name: {e}")
        return None
    finally:
        conn.close()

def add_project(proj_name, budget, proj_manager, cust_name):
    """
    Add a new project to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Validate project_name
            if len(proj_name) < 6 or len(proj_name) > 18:
                return False, "Project name must be between 6-18 characters"
            
            # Validate project_manager
            if len(proj_manager) < 6 or len(proj_manager) > 18:
                return False, "Project manager name must be between 6-18 characters"
            
            # Check if project_name already exists
            cur.execute("SELECT COUNT(*) FROM project WHERE project_name = %s", (proj_name,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Project name already exists"
            
            # Check if cust_name exists in customer table
            cur.execute("SELECT COUNT(*) FROM customer WHERE cust_name = %s", (cust_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Customer does not exist"
            
            # Insert new project
            cur.execute("""
                INSERT INTO project (project_name, budget, project_manager, cust_name) 
                VALUES (%s, %s, %s, %s)
            """, (proj_name, budget, proj_manager, cust_name))
            conn.commit()
            return True, "Project added successfully"
    except Exception as e:
        print(f"❌ Error adding project: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_project(proj_id, proj_name, budget, proj_manager, cust_name):
    """
    Update project information
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if project exists
            cur.execute("SELECT COUNT(*) FROM project WHERE project_id = %s", (proj_id,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Project not found"
            
            # Check if cust_name exists in customer table
            cur.execute("SELECT COUNT(*) FROM customer WHERE cust_name = %s", (cust_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Customer does not exist"
            
            # Update project
            cur.execute("""
                UPDATE project 
                SET project_name = %s, budget = %s, project_manager = %s, cust_name = %s 
                WHERE project_id = %s
            """, (proj_name, budget, proj_manager, cust_name, proj_id))
            conn.commit()
            return True, "Project updated successfully"
    except Exception as e:
        print(f"❌ Error updating project: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_project(proj_id):
    """
    Delete project by ID
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if project exists
            cur.execute("SELECT COUNT(*) FROM project WHERE project_id = %s", (proj_id,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Project not found"
            
            # Delete project
            cur.execute("DELETE FROM project WHERE project_id = %s", (proj_id,))
            conn.commit()
            return True, "Project deleted successfully"
    except Exception as e:
        print(f"❌ Error deleting project: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close() 