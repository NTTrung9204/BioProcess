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
                    proj_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    proj_name VARCHAR(100) NOT NULL UNIQUE,
                    proj_desc TEXT,
                    cust_name VARCHAR(18) REFERENCES customer(cust_name),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    proj_status VARCHAR(20) CHECK (proj_status IN ('active', 'completed', 'archived')) DEFAULT 'active'
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
                SELECT proj_id, proj_name, proj_desc, cust_name, created_at, proj_status
                FROM project
                ORDER BY created_at DESC
            """)
            projects = cur.fetchall()
            
            result = []
            for project in projects:
                result.append({
                    "proj_id": project[0],
                    "proj_name": project[1],
                    "proj_desc": project[2],
                    "cust_name": project[3],
                    "created_at": project[4],
                    "proj_status": project[5]
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
                SELECT proj_id, proj_name, proj_desc, cust_name, created_at, proj_status
                FROM project
                WHERE proj_id = %s
            """, (proj_id,))
            project = cur.fetchone()
            
            if project:
                return {
                    "proj_id": project[0],
                    "proj_name": project[1],
                    "proj_desc": project[2],
                    "cust_name": project[3],
                    "created_at": project[4],
                    "proj_status": project[5]
                }
            return None
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
                SELECT proj_id, proj_name, proj_desc, cust_name, created_at, proj_status
                FROM project
                WHERE proj_name = %s
            """, (proj_name,))
            project = cur.fetchone()
            
            if project:
                return {
                    "proj_id": project[0],
                    "proj_name": project[1],
                    "proj_desc": project[2],
                    "cust_name": project[3],
                    "created_at": project[4],
                    "proj_status": project[5]
                }
            return None
    except Exception as e:
        print(f"❌ Error getting project by name: {e}")
        return None
    finally:
        conn.close()

def add_project(proj_name, proj_desc, cust_name):
    """
    Add a new project to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if project name exists
            cur.execute("SELECT COUNT(*) FROM project WHERE proj_name = %s", (proj_name,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Project name already exists"
            
            # Check if customer exists
            if cust_name:
                cur.execute("SELECT COUNT(*) FROM customer WHERE cust_name = %s", (cust_name,))
                count = cur.fetchone()[0]
                if count == 0:
                    return False, "Customer does not exist"
            
            # Generate project ID
            proj_id = str(uuid.uuid4())
            
            # Insert project
            cur.execute("""
                INSERT INTO project (proj_id, proj_name, proj_desc, cust_name)
                VALUES (%s, %s, %s, %s)
            """, (proj_id, proj_name, proj_desc, cust_name))
            conn.commit()
            
            return True, "Project created successfully", proj_id
    except Exception as e:
        print(f"❌ Error adding project: {e}")
        return False, f"Error: {str(e)}", None
    finally:
        conn.close()

def update_project(proj_id, proj_name, proj_desc, cust_name, proj_status):
    """
    Update project information
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if project exists
            cur.execute("SELECT COUNT(*) FROM project WHERE proj_id = %s", (proj_id,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Project not found"
            
            # Check if project name is unique
            cur.execute("SELECT COUNT(*) FROM project WHERE proj_name = %s AND proj_id != %s", (proj_name, proj_id))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Project name already exists"
            
            # Check if customer exists
            if cust_name:
                cur.execute("SELECT COUNT(*) FROM customer WHERE cust_name = %s", (cust_name,))
                count = cur.fetchone()[0]
                if count == 0:
                    return False, "Customer does not exist"
            
            # Validate project status
            if proj_status not in ['active', 'completed', 'archived']:
                return False, "Invalid project status"
            
            # Update project
            cur.execute("""
                UPDATE project
                SET proj_name = %s, proj_desc = %s, cust_name = %s, proj_status = %s
                WHERE proj_id = %s
            """, (proj_name, proj_desc, cust_name, proj_status, proj_id))
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
            cur.execute("SELECT COUNT(*) FROM project WHERE proj_id = %s", (proj_id,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Project not found"
            
            # Delete project
            cur.execute("DELETE FROM project WHERE proj_id = %s", (proj_id,))
            conn.commit()
            
            return True, "Project deleted successfully"
    except Exception as e:
        print(f"❌ Error deleting project: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close() 