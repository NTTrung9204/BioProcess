from app.repositories.database import get_db_connection
from app.config import PostgresConfig
import uuid

def create_catalyst_table():
    """
    Create the catalyst table in the database
    """
    print("🔧 Creating catalyst table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS catalyst (
                    catalyst_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    catalyst_name VARCHAR(50) UNIQUE,
                    provider TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table catalyst created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating catalyst table: {e}")
        return False
    finally:
        conn.close()

def get_all_catalysts():
    """
    Get all catalysts from the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT catalyst_id, catalyst_name, provider, created_at 
                FROM catalyst 
                ORDER BY catalyst_name
            """)
            catalysts = cur.fetchall()
            
            result = []
            for catalyst in catalysts:
                result.append({
                    "catalyst_id": catalyst[0],
                    "catalyst_name": catalyst[1],
                    "provider": catalyst[2],
                    "created_at": catalyst[3]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting catalysts: {e}")
        return []
    finally:
        conn.close()

def get_catalyst_by_name(catalyst_name):
    """
    Get catalyst by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT catalyst_id, catalyst_name, provider, created_at 
                FROM catalyst 
                WHERE catalyst_name = %s
            """, (catalyst_name,))
            catalyst = cur.fetchone()
            
            if catalyst:
                return {
                    "catalyst_id": catalyst[0],
                    "catalyst_name": catalyst[1],
                    "provider": catalyst[2],
                    "created_at": catalyst[3]
                }
            return None
    except Exception as e:
        print(f"❌ Error getting catalyst by name: {e}")
        return None
    finally:
        conn.close()

def add_catalyst(catalyst_name, provider):
    """
    Add a new catalyst to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if catalyst_name already exists
            cur.execute("SELECT COUNT(*) FROM catalyst WHERE catalyst_name = %s", (catalyst_name,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Catalyst name already exists"
            
            # Insert new catalyst
            cur.execute("""
                INSERT INTO catalyst (catalyst_name, provider) 
                VALUES (%s, %s)
            """, (catalyst_name, provider))
            conn.commit()
            return True, "Catalyst added successfully"
    except Exception as e:
        print(f"❌ Error adding catalyst: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_catalyst(catalyst_name, provider):
    """
    Update catalyst information
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if catalyst exists
            cur.execute("SELECT COUNT(*) FROM catalyst WHERE catalyst_name = %s", (catalyst_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Catalyst not found"
            
            # Update catalyst information
            cur.execute("""
                UPDATE catalyst 
                SET provider = %s 
                WHERE catalyst_name = %s
            """, (provider, catalyst_name))
            conn.commit()
            return True, "Catalyst updated successfully"
    except Exception as e:
        print(f"❌ Error updating catalyst: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_catalyst(catalyst_name):
    """
    Delete catalyst by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if catalyst exists
            cur.execute("SELECT COUNT(*) FROM catalyst WHERE catalyst_name = %s", (catalyst_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Catalyst not found"
            
            # Delete catalyst
            cur.execute("DELETE FROM catalyst WHERE catalyst_name = %s", (catalyst_name,))
            conn.commit()
            return True, "Catalyst deleted successfully"
    except Exception as e:
        print(f"❌ Error deleting catalyst: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close() 