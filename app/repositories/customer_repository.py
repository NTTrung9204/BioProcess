from app.repositories.database import get_db_connection
from app.config import PostgresConfig

def create_customer_table():
    """
    Create the customer table in the database
    """
    print("🔧 Creating customer table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customer (
                    cust_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    cust_name VARCHAR(18) UNIQUE CHECK (LENGTH(cust_name) >= 6 AND LENGTH(cust_name) <= 18),
                    contact_infor TEXT,
                    address TEXT,
                    country VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table customer created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating customer table: {e}")
        return False
    finally:
        conn.close()

def get_all_customers():
    """
    Get all customers from the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT cust_id, cust_name, contact_infor, address, country, created_at FROM customer ORDER BY cust_name")
            customers = cur.fetchall()
            
            result = []
            for customer in customers:
                result.append({
                    "cust_id": customer[0],
                    "cust_name": customer[1],
                    "contact_infor": customer[2],
                    "address": customer[3],
                    "country": customer[4],
                    "created_at": customer[5]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting customers: {e}")
        return []
    finally:
        conn.close()

def get_customer_by_name(cust_name):
    """
    Get customer by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT cust_id, cust_name, contact_infor, address, country, created_at FROM customer WHERE cust_name = %s", (cust_name,))
            customer = cur.fetchone()
            
            if customer:
                return {
                    "cust_id": customer[0],
                    "cust_name": customer[1],
                    "contact_infor": customer[2],
                    "address": customer[3],
                    "country": customer[4],
                    "created_at": customer[5]
                }
            return None
    except Exception as e:
        print(f"❌ Error getting customer by name: {e}")
        return None
    finally:
        conn.close()

def add_customer(cust_name, contact_infor, address, country):
    """
    Add a new customer to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            if len(cust_name) < 6 or len(cust_name) > 18:
                return False, "Customer name must be between 6-18 characters"
            
            cur.execute("SELECT COUNT(*) FROM customer WHERE cust_name = %s", (cust_name,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Customer name already exists"
            
            cur.execute("""
                INSERT INTO customer (cust_name, contact_infor, address, country) 
                VALUES (%s, %s, %s, %s)
            """, (cust_name, contact_infor, address, country))
            conn.commit()
            return True, "Add customer successfully"
    except Exception as e:
        print(f"❌ Error adding customer: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_customer(cust_name, contact_infor, address, country):
    """
    Update customer information
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if customer exists
            cur.execute("SELECT COUNT(*) FROM customer WHERE cust_name = %s", (cust_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Customer not found"
            
            # Update customer information
            cur.execute("""
                UPDATE customer 
                SET contact_infor = %s, address = %s, country = %s 
                WHERE cust_name = %s
            """, (contact_infor, address, country, cust_name))
            conn.commit()
            return True, "Update customer information successfully"
    except Exception as e:
        print(f"❌ Error updating customer: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_customer(cust_name):
    """
    Delete customer by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM customer WHERE cust_name = %s", (cust_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Customer not found"
            
            cur.execute("DELETE FROM customer WHERE cust_name = %s", (cust_name,))
            conn.commit()
            return True, "Delete customer successfully"
    except Exception as e:
        print(f"❌ Error deleting customer: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def search_customers(search_term):
    """
    Search customers by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cust_name, contact_infor 
                FROM customer 
                WHERE cust_name ILIKE %s 
                ORDER BY cust_name
                LIMIT 10
            """, (f'%{search_term}%',))
            customers = cur.fetchall()
            
            result = []
            for customer in customers:
                result.append({
                    "cust_name": customer[0],
                    "contact_infor": customer[1]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error searching customers: {e}")
        return []
    finally:
        conn.close() 