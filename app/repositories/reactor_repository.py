from app.repositories.database import get_db_connection
from app.config import PostgresConfig
import uuid
from datetime import datetime

def create_reactor_table():
    """
    Create the reactor table in the database
    """
    print("🔧 Creating reactor table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reactor (
                    reactor_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    reactor_name VARCHAR(50) UNIQUE,
                    maintenance_day TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table reactor created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating reactor table: {e}")
        return False
    finally:
        conn.close()

def get_all_reactors():
    """
    Get all reactors from the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT reactor_id, reactor_name, maintenance_day, created_at 
                FROM reactor 
                ORDER BY reactor_name
            """)
            reactors = cur.fetchall()
            
            result = []
            for reactor in reactors:
                result.append({
                    "reactor_id": reactor[0],
                    "reactor_name": reactor[1],
                    "maintenance_day": reactor[2],
                    "created_at": reactor[3]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting reactors: {e}")
        return []
    finally:
        conn.close()

def get_reactor_by_name(reactor_name):
    """
    Get reactor by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT reactor_id, reactor_name, maintenance_day, created_at 
                FROM reactor 
                WHERE reactor_name = %s
            """, (reactor_name,))
            reactor = cur.fetchone()
            
            if reactor:
                return {
                    "reactor_id": reactor[0],
                    "reactor_name": reactor[1],
                    "maintenance_day": reactor[2],
                    "created_at": reactor[3]
                }
            return None
    except Exception as e:
        print(f"❌ Error getting reactor by name: {e}")
        return None
    finally:
        conn.close()

def add_reactor(reactor_name, maintenance_day):
    """
    Add a new reactor to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Validate maintenance_day
            try:
                # Convert the string datetime to a datetime object if it's a string
                if isinstance(maintenance_day, str):
                    maintenance_day = datetime.fromisoformat(maintenance_day.replace('Z', '+00:00'))
            except ValueError:
                return False, "Invalid maintenance date format. Use YYYY-MM-DD HH:MM:SS format."
            
            # Check if reactor_name already exists
            cur.execute("SELECT COUNT(*) FROM reactor WHERE reactor_name = %s", (reactor_name,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Reactor name already exists"
            
            # Insert new reactor
            cur.execute("""
                INSERT INTO reactor (reactor_name, maintenance_day) 
                VALUES (%s, %s)
            """, (reactor_name, maintenance_day))
            conn.commit()
            return True, "Reactor added successfully"
    except Exception as e:
        print(f"❌ Error adding reactor: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_reactor(reactor_name, maintenance_day):
    """
    Update reactor information
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Validate maintenance_day
            try:
                # Convert the string datetime to a datetime object if it's a string
                if isinstance(maintenance_day, str):
                    maintenance_day = datetime.fromisoformat(maintenance_day.replace('Z', '+00:00'))
            except ValueError:
                return False, "Invalid maintenance date format. Use YYYY-MM-DD HH:MM:SS format."
                
            # Check if reactor exists
            cur.execute("SELECT COUNT(*) FROM reactor WHERE reactor_name = %s", (reactor_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Reactor not found"
            
            # Update reactor information
            cur.execute("""
                UPDATE reactor 
                SET maintenance_day = %s 
                WHERE reactor_name = %s
            """, (maintenance_day, reactor_name))
            conn.commit()
            return True, "Reactor updated successfully"
    except Exception as e:
        print(f"❌ Error updating reactor: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_reactor(reactor_name):
    """
    Delete reactor by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if reactor exists
            cur.execute("SELECT COUNT(*) FROM reactor WHERE reactor_name = %s", (reactor_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Reactor not found"
            
            # Delete reactor
            cur.execute("DELETE FROM reactor WHERE reactor_name = %s", (reactor_name,))
            conn.commit()
            return True, "Reactor deleted successfully"
    except Exception as e:
        print(f"❌ Error deleting reactor: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close() 