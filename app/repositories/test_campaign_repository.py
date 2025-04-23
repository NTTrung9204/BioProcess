from app.repositories.database import get_db_connection
from app.config import PostgresConfig
import uuid
import random
import string

def create_test_campaign_table():
    """
    Create the test_campaign table in the database
    """
    print("🔧 Creating test_campaign table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_campaign (
                    test_campaign_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    test_campaign_name VARCHAR(24) UNIQUE CHECK (LENGTH(test_campaign_name) >= 8 AND LENGTH(test_campaign_name) <= 24),
                    batch_id CHAR(8) UNIQUE,
                    operator_id UUID REFERENCES operator(operator_id) ON DELETE RESTRICT,
                    reactor_id UUID REFERENCES reactor(reactor_id) ON DELETE RESTRICT,
                    feed_id UUID REFERENCES feed(feed_id) ON DELETE RESTRICT,
                    catalyst_id UUID REFERENCES catalyst(catalyst_id) ON DELETE RESTRICT,
                    project_id UUID REFERENCES project(project_id) ON DELETE RESTRICT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table test_campaign created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating test_campaign table: {e}")
        return False
    finally:
        conn.close()

def generate_batch_id():
    """
    Generate a unique batch ID consisting of 8 alphanumeric characters
    """
    chars = string.ascii_uppercase + string.digits
    while True:
        # Generate a random 8-character string
        batch_id = ''.join(random.choice(chars) for _ in range(8))
        
        # Check if it's already in use
        conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
        if conn is None:
            # If can't connect, generate a new one and hope for the best
            continue
            
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM test_campaign WHERE batch_id = %s", (batch_id,))
                if cur.fetchone() is None:
                    # Batch ID is not in use, return it
                    return batch_id
        finally:
            conn.close()

def get_all_test_campaigns():
    """
    Get all test campaigns from the database with related entity names
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    tc.test_campaign_id, 
                    tc.test_campaign_name, 
                    tc.batch_id,
                    o.operator_name,
                    r.reactor_name,
                    f.feed_name,
                    c.catalyst_name,
                    cu.cust_name,
                    p.project_name,
                    tc.created_at
                FROM test_campaign tc
                JOIN operator o ON tc.operator_id = o.operator_id
                JOIN reactor r ON tc.reactor_id = r.reactor_id
                JOIN feed f ON tc.feed_id = f.feed_id
                JOIN catalyst c ON tc.catalyst_id = c.catalyst_id
                JOIN project p ON tc.project_id = p.project_id
                JOIN customer cu ON p.customer_id = cu.cust_id
                ORDER BY tc.created_at DESC
            """)
            campaigns = cur.fetchall()
            
            result = []
            for campaign in campaigns:
                result.append({
                    "test_campaign_id": campaign[0],
                    "test_campaign_name": campaign[1],
                    "batch_id": campaign[2],
                    "operator_name": campaign[3],
                    "reactor_name": campaign[4],
                    "feed_name": campaign[5],
                    "catalyst_name": campaign[6],
                    "customer_name": campaign[7],
                    "project_name": campaign[8],
                    "created_at": campaign[9]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting test campaigns: {e}")
        return []
    finally:
        conn.close()

def get_test_campaigns_paginated(page=1, per_page=10, search_term=None):
    """
    Get paginated test campaigns with optional search filter
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return [], 0
    
    offset = (page - 1) * per_page
    
    try:
        with conn.cursor() as cur:
            # Count total records with or without search
            if search_term:
                search_pattern = f"%{search_term}%"
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM test_campaign tc
                    WHERE tc.test_campaign_name ILIKE %s OR tc.batch_id ILIKE %s
                """, (search_pattern, search_pattern))
            else:
                cur.execute("SELECT COUNT(*) FROM test_campaign")
                
            total_count = cur.fetchone()[0]
            
            # Get paginated records with joins to get names
            if search_term:
                search_pattern = f"%{search_term}%"
                cur.execute("""
                    SELECT 
                        tc.test_campaign_id, 
                        tc.test_campaign_name, 
                        tc.batch_id,
                        o.operator_name,
                        r.reactor_name,
                        f.feed_name,
                        c.catalyst_name,
                        cu.cust_name,
                        p.project_name,
                        tc.created_at
                    FROM test_campaign tc
                    JOIN operator o ON tc.operator_id = o.operator_id
                    JOIN reactor r ON tc.reactor_id = r.reactor_id
                    JOIN feed f ON tc.feed_id = f.feed_id
                    JOIN catalyst c ON tc.catalyst_id = c.catalyst_id
                    JOIN project p ON tc.project_id = p.project_id
                    JOIN customer cu ON p.customer_id = cu.cust_id
                    WHERE tc.test_campaign_name ILIKE %s OR tc.batch_id ILIKE %s
                    ORDER BY tc.created_at DESC
                    LIMIT %s OFFSET %s
                """, (search_pattern, search_pattern, per_page, offset))
            else:
                cur.execute("""
                    SELECT 
                        tc.test_campaign_id, 
                        tc.test_campaign_name, 
                        tc.batch_id,
                        o.operator_name,
                        r.reactor_name,
                        f.feed_name,
                        c.catalyst_name,
                        cu.cust_name,
                        p.project_name,
                        tc.created_at
                    FROM test_campaign tc
                    JOIN operator o ON tc.operator_id = o.operator_id
                    JOIN reactor r ON tc.reactor_id = r.reactor_id
                    JOIN feed f ON tc.feed_id = f.feed_id
                    JOIN catalyst c ON tc.catalyst_id = c.catalyst_id
                    JOIN project p ON tc.project_id = p.project_id
                    JOIN customer cu ON p.customer_id = cu.cust_id
                    ORDER BY tc.created_at DESC
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                
            campaigns = cur.fetchall()
            
            result = []
            for campaign in campaigns:
                result.append({
                    "test_campaign_id": campaign[0],
                    "test_campaign_name": campaign[1],
                    "batch_id": campaign[2],
                    "operator_name": campaign[3],
                    "reactor_name": campaign[4],
                    "feed_name": campaign[5],
                    "catalyst_name": campaign[6],
                    "customer_name": campaign[7],
                    "project_name": campaign[8],
                    "created_at": campaign[9]
                })
            
            return result, total_count
    except Exception as e:
        print(f"❌ Error getting paginated test campaigns: {e}")
        return [], 0
    finally:
        conn.close()

def get_test_campaign_by_id(test_campaign_id):
    """
    Get a specific test campaign by ID
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    tc.test_campaign_id, 
                    tc.test_campaign_name, 
                    tc.batch_id,
                    tc.operator_id, o.operator_name,
                    tc.reactor_id, r.reactor_name,
                    tc.feed_id, f.feed_name,
                    tc.catalyst_id, c.catalyst_name,
                    cu.cust_id, cu.cust_name,
                    tc.project_id, p.project_name,
                    tc.created_at
                FROM test_campaign tc
                JOIN operator o ON tc.operator_id = o.operator_id
                JOIN reactor r ON tc.reactor_id = r.reactor_id
                JOIN feed f ON tc.feed_id = f.feed_id
                JOIN catalyst c ON tc.catalyst_id = c.catalyst_id
                JOIN project p ON tc.project_id = p.project_id
                JOIN customer cu ON p.customer_id = cu.cust_id
                WHERE tc.test_campaign_id = %s
            """, (test_campaign_id,))
            
            campaign = cur.fetchone()
            
            if not campaign:
                return None
                
            return {
                "test_campaign_id": campaign[0],
                "test_campaign_name": campaign[1],
                "batch_id": campaign[2],
                "operator_id": campaign[3],
                "operator_name": campaign[4],
                "reactor_id": campaign[5],
                "reactor_name": campaign[6],
                "feed_id": campaign[7],
                "feed_name": campaign[8],
                "catalyst_id": campaign[9],
                "catalyst_name": campaign[10],
                "customer_id": campaign[11],
                "customer_name": campaign[12],
                "project_id": campaign[13],
                "project_name": campaign[14],
                "created_at": campaign[15]
            }
    except Exception as e:
        print(f"❌ Error getting test campaign by ID: {e}")
        return None
    finally:
        conn.close()

def add_test_campaign(test_campaign_name, operator_id, reactor_id, feed_id, catalyst_id, project_id):
    """
    Add a new test campaign to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database", None
    
    try:
        with conn.cursor() as cur:
            # Validate test_campaign_name
            if len(test_campaign_name) < 8 or len(test_campaign_name) > 24:
                return False, "Test campaign name must be between 8-24 characters", None
            
            # Check if test_campaign_name already exists
            cur.execute("SELECT 1 FROM test_campaign WHERE test_campaign_name = %s", (test_campaign_name,))
            if cur.fetchone():
                return False, "Test campaign name already exists", None
            
            # Generate unique batch_id
            batch_id = generate_batch_id()
            
            # Insert new test campaign
            cur.execute("""
                INSERT INTO test_campaign (
                    test_campaign_name, 
                    batch_id, 
                    operator_id, 
                    reactor_id, 
                    feed_id, 
                    catalyst_id, 
                    project_id
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING test_campaign_id, batch_id
            """, (
                test_campaign_name, 
                batch_id, 
                operator_id, 
                reactor_id, 
                feed_id, 
                catalyst_id, 
                project_id
            ))
            
            result = cur.fetchone()
            conn.commit()
            
            if result:
                test_campaign_id, batch_id = result
                return True, "Test campaign added successfully", {"test_campaign_id": test_campaign_id, "batch_id": batch_id}
            else:
                return False, "Failed to retrieve test campaign ID", None
    except Exception as e:
        conn.rollback()
        print(f"❌ Error adding test campaign: {e}")
        return False, f"Error: {str(e)}", None
    finally:
        conn.close()

def update_test_campaign(test_campaign_id, test_campaign_name, operator_id, reactor_id, feed_id, catalyst_id, project_id):
    """
    Update an existing test campaign
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if test campaign exists
            cur.execute("SELECT 1 FROM test_campaign WHERE test_campaign_id = %s", (test_campaign_id,))
            if not cur.fetchone():
                return False, "Test campaign not found"
            
            # Validate test_campaign_name
            if len(test_campaign_name) < 8 or len(test_campaign_name) > 24:
                return False, "Test campaign name must be between 8-24 characters"
            
            # Check if new name would conflict with existing one
            cur.execute("""
                SELECT 1 FROM test_campaign 
                WHERE test_campaign_name = %s AND test_campaign_id != %s
            """, (test_campaign_name, test_campaign_id))
            if cur.fetchone():
                return False, "Test campaign name already exists"
            
            # Update test campaign
            cur.execute("""
                UPDATE test_campaign 
                SET 
                    test_campaign_name = %s,
                    operator_id = %s,
                    reactor_id = %s,
                    feed_id = %s,
                    catalyst_id = %s,
                    project_id = %s
                WHERE test_campaign_id = %s
            """, (
                test_campaign_name,
                operator_id,
                reactor_id,
                feed_id,
                catalyst_id,
                project_id,
                test_campaign_id
            ))
            
            conn.commit()
            return True, "Test campaign updated successfully"
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating test campaign: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_test_campaign(test_campaign_id):
    """
    Delete a test campaign by ID
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if test campaign exists
            cur.execute("SELECT 1 FROM test_campaign WHERE test_campaign_id = %s", (test_campaign_id,))
            if not cur.fetchone():
                return False, "Test campaign not found"
            
            # Delete test campaign
            cur.execute("DELETE FROM test_campaign WHERE test_campaign_id = %s", (test_campaign_id,))
            
            conn.commit()
            return True, "Test campaign deleted successfully"
    except Exception as e:
        conn.rollback()
        print(f"❌ Error deleting test campaign: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close() 

def get_batch_id_exists(batch_id):
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM test_campaign WHERE batch_id = %s", (batch_id,))
            return cur.fetchone() is not None
    except Exception as e:
        print(f"❌ Error checking batch ID: {e}")
        return False
    finally:
        conn.close()

