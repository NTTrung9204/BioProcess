from app.repositories.database import get_db_connection
from app.config import PostgresConfig
import uuid

def create_operator_table():
    """
    Create the operator table in the database
    """
    print("🔧 Creating operator table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS operator (
                    operator_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    operator_name VARCHAR(18) UNIQUE CHECK (LENGTH(operator_name) >= 6 AND LENGTH(operator_name) <= 18),
                    level VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table operator created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating operator table: {e}")
        return False
    finally:
        conn.close()

def get_all_operators():
    """
    Get all operators from the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT operator_id, operator_name, level, created_at 
                FROM operator 
                ORDER BY operator_name
            """)
            operators = cur.fetchall()
            
            result = []
            for operator in operators:
                result.append({
                    "operator_id": operator[0],
                    "operator_name": operator[1],
                    "level": operator[2],
                    "created_at": operator[3]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting operators: {e}")
        return []
    finally:
        conn.close()

def get_operator_by_name(operator_name):
    """
    Get operator by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT operator_id, operator_name, level, created_at 
                FROM operator 
                WHERE operator_name = %s
            """, (operator_name,))
            operator = cur.fetchone()
            
            if operator:
                return {
                    "operator_id": operator[0],
                    "operator_name": operator[1],
                    "level": operator[2],
                    "created_at": operator[3]
                }
            return None
    except Exception as e:
        print(f"❌ Error getting operator by name: {e}")
        return None
    finally:
        conn.close()

def add_operator(operator_name, level):
    """
    Add a new operator to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Validate operator_name
            if len(operator_name) < 6 or len(operator_name) > 18:
                return False, "Operator name must be between 6-18 characters"
            
            # Check if operator_name already exists
            cur.execute("SELECT COUNT(*) FROM operator WHERE operator_name = %s", (operator_name,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Operator name already exists"
            
            # Insert new operator
            cur.execute("""
                INSERT INTO operator (operator_name, level) 
                VALUES (%s, %s)
            """, (operator_name, level))
            conn.commit()
            return True, "Operator added successfully"
    except Exception as e:
        print(f"❌ Error adding operator: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_operator(operator_name, level):
    """
    Update operator information
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if operator exists
            cur.execute("SELECT COUNT(*) FROM operator WHERE operator_name = %s", (operator_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Operator not found"
            
            # Update operator information
            cur.execute("""
                UPDATE operator 
                SET level = %s 
                WHERE operator_name = %s
            """, (level, operator_name))
            conn.commit()
            return True, "Operator updated successfully"
    except Exception as e:
        print(f"❌ Error updating operator: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_operator(operator_name):
    """
    Delete operator by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if operator exists
            cur.execute("SELECT COUNT(*) FROM operator WHERE operator_name = %s", (operator_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Operator not found"
            
            # Delete operator
            cur.execute("DELETE FROM operator WHERE operator_name = %s", (operator_name,))
            conn.commit()
            return True, "Operator deleted successfully"
    except Exception as e:
        print(f"❌ Error deleting operator: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close() 