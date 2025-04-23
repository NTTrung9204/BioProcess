from app.repositories.database import get_db_connection
from app.config import PostgresConfig

def create_feed_composition_table():
    """
    Create the feed_composition table in the database
    """
    print("🔧 Creating feed_composition table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feed_composition (
                    id UUID DEFAULT gen_random_uuid(),
                    feed_id UUID REFERENCES feed(feed_id) ON DELETE CASCADE,
                    composition TEXT NOT NULL,
                    percentage FLOAT NOT NULL CHECK (percentage > 0 AND percentage <= 1),
                    provider TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table feed_composition created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating feed_composition table: {e}")
        return False
    finally:
        conn.close()

def get_compositions_by_feed_id(feed_id):
    """
    Get all compositions for a specific feed
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, feed_id, composition, percentage, provider, created_at 
                FROM feed_composition 
                WHERE feed_id = %s
                ORDER BY percentage DESC
            """, (feed_id,))
            compositions = cur.fetchall()
            
            result = []
            for comp in compositions:
                result.append({
                    "id": comp[0],
                    "feed_id": comp[1],
                    "composition": comp[2],
                    "percentage": comp[3],
                    "provider": comp[4],
                    "created_at": comp[5]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting feed compositions: {e}")
        return []
    finally:
        conn.close()

def get_composition_by_id(composition_id):
    """
    Get composition by id
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, feed_id, composition, percentage, provider, created_at 
                FROM feed_composition 
                WHERE id = %s
            """, (composition_id,))
            comp = cur.fetchone()
            
            if comp:
                return {
                    "id": comp[0],
                    "feed_id": comp[1],
                    "composition": comp[2],
                    "percentage": comp[3],
                    "provider": comp[4],
                    "created_at": comp[5]
                }
            return None
    except Exception as e:
        print(f"❌ Error getting composition by id: {e}")
        return None
    finally:
        conn.close()

def get_total_percentage_for_feed(feed_id):
    """
    Calculate the total percentage of all compositions for a feed
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return 0
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(percentage), 0) 
                FROM feed_composition 
                WHERE feed_id = %s
            """, (feed_id,))
            result = cur.fetchone()
            return float(result[0]) if result else 0
    except Exception as e:
        print(f"❌ Error calculating total percentage: {e}")
        return 0
    finally:
        conn.close()

def add_composition(feed_id, composition, percentage, provider):
    """
    Add a new composition to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        # Validate percentage
        try:
            percentage = float(percentage)
            if percentage <= 0 or percentage > 1:
                return False, "Percentage must be between 0 and 1"
        except ValueError:
            return False, "Percentage must be a number"
        
        # Check if feed exists
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM feed WHERE feed_id = %s", (feed_id,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Feed not found"
            
            # Calculate current total percentage
            current_total = get_total_percentage_for_feed(feed_id)
            new_total = current_total + percentage
            
            if new_total > 1:
                return False, f"Total percentage would exceed 100%. Current total: {current_total*100:.2f}%, Trying to add: {percentage*100:.2f}%, Maximum allowed: {(1-current_total)*100:.2f}%"
            
            # Insert new composition
            cur.execute("""
                INSERT INTO feed_composition (feed_id, composition, percentage, provider) 
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (feed_id, composition, percentage, provider))
            
            new_id = cur.fetchone()[0]
            conn.commit()
            
            return True, f"Composition added successfully. Current total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error adding composition: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_composition(composition_id, composition, percentage, provider):
    """
    Update a composition
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        # Validate percentage
        try:
            percentage = float(percentage)
            if percentage <= 0 or percentage > 1:
                return False, "Percentage must be between 0 and 1"
        except ValueError:
            return False, "Percentage must be a number"
        
        with conn.cursor() as cur:
            # Check if composition exists and get feed_id and current percentage
            cur.execute("""
                SELECT feed_id, percentage 
                FROM feed_composition 
                WHERE id = %s
            """, (composition_id,))
            
            comp_data = cur.fetchone()
            if not comp_data:
                return False, "Composition not found"
                
            feed_id, old_percentage = comp_data
            
            # Calculate new total percentage
            current_total = get_total_percentage_for_feed(feed_id)
            new_total = current_total - old_percentage + percentage
            
            if new_total > 1:
                return False, f"Total percentage would exceed 100%. Current total without this composition: {(current_total-old_percentage)*100:.2f}%, Trying to set: {percentage*100:.2f}%, Maximum allowed: {(1-(current_total-old_percentage))*100:.2f}%"
            
            # Update composition
            cur.execute("""
                UPDATE feed_composition 
                SET composition = %s, percentage = %s, provider = %s 
                WHERE id = %s
            """, (composition, percentage, provider, composition_id))
            
            conn.commit()
            return True, f"Composition updated successfully. New total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error updating composition: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_composition(composition_id):
    """
    Delete a composition
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if composition exists
            cur.execute("SELECT feed_id FROM feed_composition WHERE id = %s", (composition_id,))
            result = cur.fetchone()
            if not result:
                return False, "Composition not found"
                
            feed_id = result[0]
            
            # Delete composition
            cur.execute("DELETE FROM feed_composition WHERE id = %s", (composition_id,))
            conn.commit()
            
            # Calculate new total
            new_total = get_total_percentage_for_feed(feed_id)
            
            return True, f"Composition deleted successfully. Remaining total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error deleting composition: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def get_feed_with_compositions(feed_id):
    """
    Get feed details with all its compositions
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            # Get feed information
            cur.execute("""
                SELECT feed_id, feed_name, provider, created_at 
                FROM feed 
                WHERE feed_id = %s
            """, (feed_id,))
            
            feed_data = cur.fetchone()
            if not feed_data:
                return None
                
            feed = {
                "feed_id": feed_data[0],
                "feed_name": feed_data[1],
                "provider": feed_data[2],
                "created_at": feed_data[3],
                "compositions": []
            }
            
            # Get compositions
            compositions = get_compositions_by_feed_id(feed_id)
            feed["compositions"] = compositions
            
            # Calculate total percentage
            total_percentage = sum(comp["percentage"] for comp in compositions)
            feed["total_percentage"] = total_percentage
            
            return feed
    except Exception as e:
        print(f"❌ Error getting feed with compositions: {e}")
        return None
    finally:
        conn.close() 