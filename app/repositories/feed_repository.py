from app.repositories.database import get_db_connection
from app.config import PostgresConfig
import uuid

def create_feed_table():
    """
    Create the feed table in the database
    """
    print("🔧 Creating feed table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feed (
                    feed_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    feed_name VARCHAR(50) UNIQUE,
                    provider TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table feed created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating feed table: {e}")
        return False
    finally:
        conn.close()

def get_all_feeds():
    """
    Get all feeds from the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT feed_id, feed_name, provider, created_at 
                FROM feed 
                ORDER BY feed_name
            """)
            feeds = cur.fetchall()
            
            result = []
            for feed in feeds:
                result.append({
                    "feed_id": feed[0],
                    "feed_name": feed[1],
                    "provider": feed[2],
                    "created_at": feed[3]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting feeds: {e}")
        return []
    finally:
        conn.close()

def get_feed_by_name(feed_name):
    """
    Get feed by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT feed_id, feed_name, provider, created_at 
                FROM feed 
                WHERE feed_name = %s
            """, (feed_name,))
            feed = cur.fetchone()
            
            if feed:
                return {
                    "feed_id": feed[0],
                    "feed_name": feed[1],
                    "provider": feed[2],
                    "created_at": feed[3]
                }
            return None
    except Exception as e:
        print(f"❌ Error getting feed by name: {e}")
        return None
    finally:
        conn.close()

def add_feed(feed_name, provider):
    """
    Add a new feed to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if feed_name already exists
            cur.execute("SELECT COUNT(*) FROM feed WHERE feed_name = %s", (feed_name,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Feed name already exists"
            
            # Insert new feed
            cur.execute("""
                INSERT INTO feed (feed_name, provider) 
                VALUES (%s, %s)
            """, (feed_name, provider))
            conn.commit()
            return True, "Feed added successfully"
    except Exception as e:
        print(f"❌ Error adding feed: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_feed(feed_name, provider):
    """
    Update feed information
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if feed exists
            cur.execute("SELECT COUNT(*) FROM feed WHERE feed_name = %s", (feed_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Feed not found"
            
            # Update feed information
            cur.execute("""
                UPDATE feed 
                SET provider = %s 
                WHERE feed_name = %s
            """, (provider, feed_name))
            conn.commit()
            return True, "Feed updated successfully"
    except Exception as e:
        print(f"❌ Error updating feed: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_feed(feed_name):
    """
    Delete feed by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if feed exists
            cur.execute("SELECT COUNT(*) FROM feed WHERE feed_name = %s", (feed_name,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Feed not found"
            
            # Delete feed
            cur.execute("DELETE FROM feed WHERE feed_name = %s", (feed_name,))
            conn.commit()
            return True, "Feed deleted successfully"
    except Exception as e:
        print(f"❌ Error deleting feed: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close() 