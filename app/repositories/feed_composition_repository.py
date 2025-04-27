import psycopg2
from app.config import PostgresConfig
from app.repositories.database import get_db_connection
from datetime import datetime

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
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    quantity FLOAT NOT NULL CHECK (quantity >= 0),
                    viscosity FLOAT,
                    pH FLOAT,
                    density FLOAT,
                    water FLOAT,
                    provider TEXT,
                    impurity FLOAT NOT NULL CHECK (impurity >= 0 AND impurity <= 1),
                    proportion FLOAT NOT NULL CHECK (proportion >= 0 AND proportion <= 1),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table feed_composition created suffessfully")
            
            # Create the join table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feed_feed_composition (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    feed_id UUID REFERENCES feed(feed_id) ON DELETE CASCADE,
                    feed_composition_id UUID REFERENCES feed_composition(id) ON DELETE RESTRICT,
                    percentage FLOAT NOT NULL CHECK (percentage > 0 AND percentage <= 1),
                    quantity_used FLOAT NOT NULL CHECK (quantity_used > 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table feed_feed_composition created suffessfully")
            return True
    except Exception as e:
        print(f"❌ Error creating feed_composition tables: {e}")
        return False
    finally:
        conn.close()

def get_all_compositions():
    """
    Get all compositions
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, quantity, viscosity, pH, density, water, provider, impurity, proportion, created_at
                FROM feed_composition 
                ORDER BY name
            """)
            compositions = cur.fetchall()
            
            result = []
            for comp in compositions:
                # Check if composition is used in any feed
                cur.execute("""
                    SELECT COUNT(*), COALESCE(SUM(quantity_used), 0) 
                    FROM feed_feed_composition 
                    WHERE feed_composition_id = %s
                """, (comp[0],))
                usage_data = cur.fetchone()
                is_used = usage_data[0] > 0
                quantity_used = float(usage_data[1]) if usage_data[1] else 0
                
                result.append({
                    "id": comp[0],
                    "name": comp[1],
                    "quantity": comp[2],
                    "viscosity": comp[3],
                    "pH": comp[4],
                    "density": comp[5],
                    "water": comp[6],
                    "provider": comp[7],
                    "impurity": comp[8],
                    "proportion": comp[9],
                    "created_at": comp[10],
                    "is_used": is_used,
                    "quantity_used": quantity_used
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
                SELECT id, name, quantity, viscosity, pH, density, water, provider, impurity, proportion, created_at 
                FROM feed_composition 
                WHERE id = %s
            """, (composition_id,))
            comp = cur.fetchone()
            
            if comp:
                # Check if composition is used in any feed
                cur.execute("""
                    SELECT COUNT(*), COALESCE(SUM(quantity_used), 0) 
                    FROM feed_feed_composition 
                    WHERE feed_composition_id = %s
                """, (comp[0],))
                usage_data = cur.fetchone()
                is_used = usage_data[0] > 0
                quantity_used = float(usage_data[1]) if usage_data[1] else 0
                
                return {
                    "id": comp[0],
                    "name": comp[1],
                    "quantity": comp[2],
                    "viscosity": comp[3],
                    "pH": comp[4],
                    "density": comp[5],
                    "water": comp[6],
                    "provider": comp[7],
                    "impurity": comp[8],
                    "proportion": comp[9],
                    "created_at": comp[10],
                    "is_used": is_used,
                    "quantity_used": quantity_used
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
                FROM feed_feed_composition 
                WHERE feed_id = %s
            """, (feed_id,))
            result = cur.fetchone()
            return float(result[0]) if result else 0
    except Exception as e:
        print(f"❌ Error calculating total percentage: {e}")
        return 0
    finally:
        conn.close()

def add_composition(name, quantity, viscosity=None, pH=None, density=None, water=None, provider=None, impurity=0, proportion=0):
    """
    Add a new composition to the database
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        # Validate quantity
        try:
            quantity = float(quantity)
            if quantity < 0:
                return False, "Quantity must be a positive number"
        except ValueError:
            return False, "Quantity must be a number"
        
        # Insert new composition
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO feed_composition (name, quantity, viscosity, pH, density, water, provider, impurity, proportion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (name, quantity, viscosity, pH, density, water, provider, impurity, proportion))
            
            new_id = cur.fetchone()[0]
            conn.commit()
            
            return True, new_id
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "A composition with this name already exists"
    except Exception as e:
        print(f"❌ Error adding composition: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_composition(composition_id, name, quantity, viscosity=None, pH=None, density=None, water=None, provider=None, impurity=0, proportion=0):
    """
    Update a composition
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        # Validate quantity
        try:
            quantity = float(quantity)
            if quantity < 0:
                return False, "Quantity must be a positive number"
        except ValueError:
            return False, "Quantity must be a number"
        
        with conn.cursor() as cur:
            # Check if composition exists
            cur.execute("SELECT quantity FROM feed_composition WHERE id = %s", (composition_id,))
            result = cur.fetchone()
            if not result:
                return False, "Composition not found"
            
            current_quantity = float(result[0])
            
            # Check if quantity is sufficient
            cur.execute("""
                SELECT COALESCE(SUM(quantity_used), 0) 
                FROM feed_feed_composition 
                WHERE feed_composition_id = %s
            """, (composition_id,))
            result = cur.fetchone()
            used_quantity = float(result[0]) if result and result[0] else 0
            
            if quantity < used_quantity:
                return False, f"Cannot reduce quantity below {used_quantity} as it's being used by feeds"
            
            # Update composition
            current_time = datetime.now()
            cur.execute("""
                UPDATE feed_composition 
                SET name = %s, quantity = %s, viscosity = %s, pH = %s, density = %s, water = %s, 
                    provider = %s, impurity = %s, proportion = %s,
                    created_at = %s
                WHERE id = %s
            """, (name, quantity, viscosity, pH, density, water, provider, impurity, proportion, current_time, composition_id))
            
            conn.commit()
            return True, "Composition updated suffessfully"
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "A composition with this name already exists"
    except Exception as e:
        print(f"❌ Error updating composition: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def delete_composition(composition_id):
    """
    Delete a composition if it's not used in any feed
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if composition exists
            cur.execute("SELECT id FROM feed_composition WHERE id = %s", (composition_id,))
            if not cur.fetchone():
                return False, "Composition not found"
            
            # Check if composition is used in any feed
            cur.execute("""
                SELECT COUNT(*) FROM feed_feed_composition 
                WHERE feed_composition_id = %s
            """, (composition_id,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Cannot delete composition as it's being used in feeds"
            
            # Delete composition
            cur.execute("DELETE FROM feed_composition WHERE id = %s", (composition_id,))
            conn.commit()
            
            return True, "Composition deleted suffessfully"
    except Exception as e:
        print(f"❌ Error deleting composition: {e}")
        return False, f"Error: {str(e)}"
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
                SELECT ff.id, ff.feed_id, fc.id as composition_id, fc.name, 
                       ff.percentage, ff.quantity_used, fc.quantity, fc.viscosity, 
                       fc.pH, fc.density, fc.water, fc.provider, fc.impurity, fc.proportion, 
                       ff.created_at
                FROM feed_feed_composition ff
                JOIN feed_composition fc ON ff.feed_composition_id = fc.id
                WHERE ff.feed_id = %s
                ORDER BY ff.percentage DESC
            """, (feed_id,))
            compositions = cur.fetchall()

            print(compositions, "compositions", flush=True)
            
            result = []
            for comp in compositions:
                result.append({
                    "id": comp[0],
                    "feed_id": comp[1],
                    "composition_id": comp[2],
                    "name": comp[3],
                    "percentage": comp[4],
                    "quantity_used": comp[5],
                    "quantity": comp[6],
                    "viscosity": comp[7],
                    "pH": comp[8],
                    "density": comp[9],
                    "water": comp[10],
                    "provider": comp[11],
                    "impurity": comp[12],
                    "proportion": comp[13],
                    "created_at": comp[14]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting feed compositions: {e}")
        return []
    finally:
        conn.close()

def add_composition_to_feed(feed_id, composition_id, percentage, quantity_used):
    """
    Add a composition to a feed
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
        
        # Validate quantity_used
        try:
            quantity_used = float(quantity_used)
            if quantity_used <= 0:
                return False, "Quantity used must be positive"
        except ValueError:
            return False, "Quantity used must be a number"
        
        with conn.cursor() as cur:
            # Check if feed exists
            cur.execute("SELECT COUNT(*) FROM feed WHERE feed_id = %s", (feed_id,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "feed not found"
            
            # Check if composition exists and has enough quantity
            cur.execute("SELECT quantity FROM feed_composition WHERE id = %s", (composition_id,))
            result = cur.fetchone()
            if not result:
                return False, "Composition not found"
            
            total_quantity = float(result[0])
            
            # Calculate current used quantity
            cur.execute("""
                SELECT COALESCE(SUM(quantity_used), 0) 
                FROM feed_feed_composition 
                WHERE feed_composition_id = %s
            """, (composition_id,))
            result = cur.fetchone()
            current_used = float(result[0]) if result and result[0] else 0
            
            available_quantity = total_quantity - current_used
            if available_quantity < quantity_used:
                return False, f"Not enough quantity available. Available: {available_quantity}, Requested: {quantity_used}"
            
            # Calculate current total percentage
            current_total = get_total_percentage_for_feed(feed_id)
            new_total = current_total + percentage
            
            if new_total > 1:
                return False, f"Total percentage would exceed 100%. Current total: {current_total*100:.2f}%, Trying to add: {percentage*100:.2f}%, Maximum allowed: {(1-current_total)*100:.2f}%"
            
            # Check if this composition is already added to this feed
            cur.execute("""
                SELECT id FROM feed_feed_composition 
                WHERE feed_id = %s AND feed_composition_id = %s
            """, (feed_id, composition_id))
            if cur.fetchone():
                return False, "This composition is already added to this feed"
            
            # Insert new composition-feed relationship
            cur.execute("""
                INSERT INTO feed_feed_composition (feed_id, feed_composition_id, percentage, quantity_used) 
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (feed_id, composition_id, percentage, quantity_used))
            
            new_id = cur.fetchone()[0]
            conn.commit()
            
            return True, f"Composition added suffessfully to feed. Current total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error adding composition to feed: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_feed_composition(relation_id, percentage, quantity_used):
    """
    Update a feed-composition relationship
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
        
        # Validate quantity_used
        try:
            quantity_used = float(quantity_used)
            if quantity_used <= 0:
                return False, "Quantity used must be positive"
        except ValueError:
            return False, "Quantity used must be a number"
        
        with conn.cursor() as cur:
            # Check if relationship exists and get data
            cur.execute("""
                SELECT feed_id, feed_composition_id, percentage, quantity_used 
                FROM feed_feed_composition 
                WHERE id = %s
            """, (relation_id,))
            
            rel_data = cur.fetchone()
            if not rel_data:
                return False, "Relationship not found"
                
            feed_id, composition_id, old_percentage, old_quantity = rel_data
            
            # Check if composition has enough quantity
            cur.execute("SELECT quantity FROM feed_composition WHERE id = %s", (composition_id,))
            result = cur.fetchone()
            total_quantity = float(result[0])
            
            # Calculate current used quantity (excluding this relationship)
            cur.execute("""
                SELECT COALESCE(SUM(quantity_used), 0) 
                FROM feed_feed_composition 
                WHERE feed_composition_id = %s AND id != %s
            """, (composition_id, relation_id))
            result = cur.fetchone()
            current_used = float(result[0]) if result and result[0] else 0
            
            available_quantity = total_quantity - current_used
            if available_quantity < quantity_used:
                return False, f"Not enough quantity available. Available: {available_quantity}, Requested: {quantity_used}"
            
            # Calculate new total percentage
            current_total = get_total_percentage_for_feed(feed_id)
            new_total = current_total - old_percentage + percentage
            
            if new_total > 1:
                return False, f"Total percentage would exceed 100%. Current total without this composition: {(current_total-old_percentage)*100:.2f}%, Trying to set: {percentage*100:.2f}%, Maximum allowed: {(1-(current_total-old_percentage))*100:.2f}%"
            
            # Update relationship
            cur.execute("""
                UPDATE feed_feed_composition 
                SET percentage = %s, quantity_used = %s 
                WHERE id = %s
            """, (percentage, quantity_used, relation_id))
            
            conn.commit()
            return True, f"feed composition updated suffessfully. New total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error updating feed composition: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def remove_composition_from_feed(relation_id):
    """
    Remove a composition from a feed
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if relationship exists
            cur.execute("""
                SELECT feed_id FROM feed_feed_composition 
                WHERE id = %s
            """, (relation_id,))
            result = cur.fetchone()
            if not result:
                return False, "Relationship not found"
                
            feed_id = result[0]
            
            # Delete relationship
            cur.execute("DELETE FROM feed_feed_composition WHERE id = %s", (relation_id,))
            conn.commit()
            
            # Calculate new total
            new_total = get_total_percentage_for_feed(feed_id)
            
            return True, f"Composition removed from feed suffessfully. Remaining total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error removing composition from feed: {e}")
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
            print(compositions, "compositions", flush=True)
            feed["compositions"] = compositions
            
            # Calculate total percentage
            total_percentage = get_total_percentage_for_feed(feed_id)
            feed["total_percentage"] = total_percentage
            
            return feed
    except Exception as e:
        print(f"❌ Error getting feed with compositions: {e}")
        return None
    finally:
        conn.close()

def get_relation_by_id(relation_id):
    """
    Get a specific feed-composition relationship by ID
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ff.id, ff.feed_id, fc.id as composition_id, fc.name, 
                       ff.percentage, ff.quantity_used, fc.quantity, ff.created_at
                FROM feed_feed_composition ff
                JOIN feed_composition fc ON ff.feed_composition_id = fc.id
                WHERE ff.id = %s
            """, (relation_id,))
            rel = cur.fetchone()
            
            if rel:
                return {
                    "id": rel[0],
                    "feed_id": rel[1],
                    "composition_id": rel[2],
                    "composition_name": rel[3],
                    "percentage": rel[4],
                    "quantity_used": rel[5],
                    "available_quantity": rel[6],
                    "created_at": rel[7]
                }
            return None
    except Exception as e:
        print(f"❌ Error getting relationship by id: {e}")
        return None
    finally:
        conn.close()

def search_compositions_by_name(search_term):
    """
    Search compositions by name
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, quantity, viscosity, pH, density, water, provider, impurity, proportion
                FROM feed_composition 
                WHERE name ILIKE %s
                ORDER BY name
                LIMIT 10
            """, (f'%{search_term}%',))
            compositions = cur.fetchall()
            
            result = []
            for comp in compositions:
                # Check how much quantity is already used
                cur.execute("""
                    SELECT COALESCE(SUM(quantity_used), 0) 
                    FROM feed_feed_composition 
                    WHERE feed_composition_id = %s
                """, (comp[0],))
                usage_data = cur.fetchone()
                used_quantity = float(usage_data[0]) if usage_data and usage_data[0] else 0
                available_quantity = float(comp[2]) - used_quantity
                
                result.append({
                    "id": comp[0],
                    "name": comp[1],
                    "quantity": available_quantity,
                    "total_quantity": comp[2],
                    "viscosity": comp[3],
                    "pH": comp[4],
                    "density": comp[5],
                    "water": comp[6],
                    "provider": comp[7],
                    "impurity": comp[8],
                    "proportion": comp[9]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error searching compositions by name: {e}")
        return []
    finally:
        conn.close()
