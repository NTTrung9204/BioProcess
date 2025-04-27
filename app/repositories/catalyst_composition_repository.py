import psycopg2
from app.config import PostgresConfig
from app.repositories.database import get_db_connection
from datetime import datetime

def create_catalyst_composition_table():
    """
    Create the catalyst_composition table in the database
    """
    print("🔧 Creating catalyst_composition table...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS catalyst_composition (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    quantity FLOAT NOT NULL CHECK (quantity >= 0),
                    surface_area FLOAT,
                    acidity FLOAT,
                    support_type TEXT,
                    provider TEXT,
                    impurity FLOAT NOT NULL CHECK (impurity >= 0 AND impurity <= 1),
                    proportion FLOAT NOT NULL CHECK (proportion >= 0 AND proportion <= 1),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table catalyst_composition created successfully")
            
            # Create the join table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS catalyst_catalyst_composition (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    catalyst_id UUID REFERENCES catalyst(catalyst_id) ON DELETE CASCADE,
                    catalyst_composition_id UUID REFERENCES catalyst_composition(id) ON DELETE RESTRICT,
                    percentage FLOAT NOT NULL CHECK (percentage > 0 AND percentage <= 1),
                    quantity_used FLOAT NOT NULL CHECK (quantity_used > 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Table catalyst_catalyst_composition created successfully")
            return True
    except Exception as e:
        print(f"❌ Error creating catalyst_composition tables: {e}")
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
                SELECT id, name, quantity, surface_area, acidity, support_type, provider, impurity, proportion, created_at
                FROM catalyst_composition 
                ORDER BY name
            """)
            compositions = cur.fetchall()
            
            result = []
            for comp in compositions:
                # Check if composition is used in any catalyst
                cur.execute("""
                    SELECT COUNT(*), COALESCE(SUM(quantity_used), 0) 
                    FROM catalyst_catalyst_composition 
                    WHERE catalyst_composition_id = %s
                """, (comp[0],))
                usage_data = cur.fetchone()
                is_used = usage_data[0] > 0
                quantity_used = float(usage_data[1]) if usage_data[1] else 0
                
                result.append({
                    "id": comp[0],
                    "name": comp[1],
                    "quantity": comp[2],
                    "surface_area": comp[3],
                    "acidity": comp[4],
                    "support_type": comp[5],
                    "provider": comp[6],
                    "impurity": comp[7],
                    "proportion": comp[8],
                    "created_at": comp[9],
                    "is_used": is_used,
                    "quantity_used": quantity_used
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting catalyst compositions: {e}")
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
                SELECT id, name, quantity, surface_area, acidity, support_type, provider, impurity, proportion, created_at 
                FROM catalyst_composition 
                WHERE id = %s
            """, (composition_id,))
            comp = cur.fetchone()
            
            if comp:
                # Check if composition is used in any catalyst
                cur.execute("""
                    SELECT COUNT(*), COALESCE(SUM(quantity_used), 0) 
                    FROM catalyst_catalyst_composition 
                    WHERE catalyst_composition_id = %s
                """, (comp[0],))
                usage_data = cur.fetchone()
                is_used = usage_data[0] > 0
                quantity_used = float(usage_data[1]) if usage_data[1] else 0
                
                return {
                    "id": comp[0],
                    "name": comp[1],
                    "quantity": comp[2],
                    "surface_area": comp[3],
                    "acidity": comp[4],
                    "support_type": comp[5],
                    "provider": comp[6],
                    "impurity": comp[7],
                    "proportion": comp[8],
                    "created_at": comp[9],
                    "is_used": is_used,
                    "quantity_used": quantity_used
                }
            return None
    except Exception as e:
        print(f"❌ Error getting composition by id: {e}")
        return None
    finally:
        conn.close()

def get_total_percentage_for_catalyst(catalyst_id):
    """
    Calculate the total percentage of all compositions for a catalyst
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return 0
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(percentage), 0) 
                FROM catalyst_catalyst_composition 
                WHERE catalyst_id = %s
            """, (catalyst_id,))
            result = cur.fetchone()
            return float(result[0]) if result else 0
    except Exception as e:
        print(f"❌ Error calculating total percentage: {e}")
        return 0
    finally:
        conn.close()

def add_composition(name, quantity, surface_area=None, acidity=None, support_type=None, provider=None, impurity=0, proportion=0):
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
                INSERT INTO catalyst_composition (name, quantity, surface_area, acidity, support_type, provider, impurity, proportion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (name, quantity, surface_area, acidity, support_type, provider, impurity, proportion))
            
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

def update_composition(composition_id, name, quantity, surface_area=None, acidity=None, support_type=None, provider=None, impurity=0, proportion=0):
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
            cur.execute("SELECT quantity FROM catalyst_composition WHERE id = %s", (composition_id,))
            result = cur.fetchone()
            if not result:
                return False, "Composition not found"
            
            current_quantity = float(result[0])
            
            # Check if quantity is sufficient
            cur.execute("""
                SELECT COALESCE(SUM(quantity_used), 0) 
                FROM catalyst_catalyst_composition 
                WHERE catalyst_composition_id = %s
            """, (composition_id,))
            result = cur.fetchone()
            used_quantity = float(result[0]) if result and result[0] else 0
            
            if quantity < used_quantity:
                return False, f"Cannot reduce quantity below {used_quantity} as it's being used by catalysts"
            
            # Update composition
            current_time = datetime.now()
            cur.execute("""
                UPDATE catalyst_composition 
                SET name = %s, quantity = %s, surface_area = %s, acidity = %s, 
                    support_type = %s, provider = %s, impurity = %s, proportion = %s,
                    created_at = %s
                WHERE id = %s
            """, (name, quantity, surface_area, acidity, support_type, provider, impurity, proportion, current_time, composition_id))
            
            conn.commit()
            return True, "Composition updated successfully"
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
    Delete a composition if it's not used in any catalyst
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if composition exists
            cur.execute("SELECT id FROM catalyst_composition WHERE id = %s", (composition_id,))
            if not cur.fetchone():
                return False, "Composition not found"
            
            # Check if composition is used in any catalyst
            cur.execute("""
                SELECT COUNT(*) FROM catalyst_catalyst_composition 
                WHERE catalyst_composition_id = %s
            """, (composition_id,))
            count = cur.fetchone()[0]
            if count > 0:
                return False, "Cannot delete composition as it's being used in catalysts"
            
            # Delete composition
            cur.execute("DELETE FROM catalyst_composition WHERE id = %s", (composition_id,))
            conn.commit()
            
            return True, "Composition deleted successfully"
    except Exception as e:
        print(f"❌ Error deleting composition: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def get_compositions_by_catalyst_id(catalyst_id):
    """
    Get all compositions for a specific catalyst
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cc.id, cc.catalyst_id, c.id as composition_id, c.name, 
                       cc.percentage, cc.quantity_used, c.quantity, c.surface_area, 
                       c.acidity, c.support_type, c.provider, c.impurity, c.proportion, 
                       cc.created_at
                FROM catalyst_catalyst_composition cc
                JOIN catalyst_composition c ON cc.catalyst_composition_id = c.id
                WHERE cc.catalyst_id = %s
                ORDER BY cc.percentage DESC
            """, (catalyst_id,))
            compositions = cur.fetchall()

            print(compositions, "compositions", flush=True)
            
            result = []
            for comp in compositions:
                result.append({
                    "id": comp[0],
                    "catalyst_id": comp[1],
                    "composition_id": comp[2],
                    "name": comp[3],
                    "percentage": comp[4],
                    "quantity_used": comp[5],
                    "quantity": comp[6],
                    "surface_area": comp[7],
                    "acidity": comp[8],
                    "support_type": comp[9],
                    "provider": comp[10],
                    "impurity": comp[11],
                    "created_at": comp[10]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error getting catalyst compositions: {e}")
        return []
    finally:
        conn.close()

def add_composition_to_catalyst(catalyst_id, composition_id, percentage, quantity_used):
    """
    Add a composition to a catalyst
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
            # Check if catalyst exists
            cur.execute("SELECT COUNT(*) FROM catalyst WHERE catalyst_id = %s", (catalyst_id,))
            count = cur.fetchone()[0]
            if count == 0:
                return False, "Catalyst not found"
            
            # Check if composition exists and has enough quantity
            cur.execute("SELECT quantity FROM catalyst_composition WHERE id = %s", (composition_id,))
            result = cur.fetchone()
            if not result:
                return False, "Composition not found"
            
            total_quantity = float(result[0])
            
            # Calculate current used quantity
            cur.execute("""
                SELECT COALESCE(SUM(quantity_used), 0) 
                FROM catalyst_catalyst_composition 
                WHERE catalyst_composition_id = %s
            """, (composition_id,))
            result = cur.fetchone()
            current_used = float(result[0]) if result and result[0] else 0
            
            available_quantity = total_quantity - current_used
            if available_quantity < quantity_used:
                return False, f"Not enough quantity available. Available: {available_quantity}, Requested: {quantity_used}"
            
            # Calculate current total percentage
            current_total = get_total_percentage_for_catalyst(catalyst_id)
            new_total = current_total + percentage
            
            if new_total > 1:
                return False, f"Total percentage would exceed 100%. Current total: {current_total*100:.2f}%, Trying to add: {percentage*100:.2f}%, Maximum allowed: {(1-current_total)*100:.2f}%"
            
            # Check if this composition is already added to this catalyst
            cur.execute("""
                SELECT id FROM catalyst_catalyst_composition 
                WHERE catalyst_id = %s AND catalyst_composition_id = %s
            """, (catalyst_id, composition_id))
            if cur.fetchone():
                return False, "This composition is already added to this catalyst"
            
            # Insert new composition-catalyst relationship
            cur.execute("""
                INSERT INTO catalyst_catalyst_composition (catalyst_id, catalyst_composition_id, percentage, quantity_used) 
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (catalyst_id, composition_id, percentage, quantity_used))
            
            new_id = cur.fetchone()[0]
            conn.commit()
            
            return True, f"Composition added successfully to catalyst. Current total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error adding composition to catalyst: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def update_catalyst_composition(relation_id, percentage, quantity_used):
    """
    Update a catalyst-composition relationship
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
                SELECT catalyst_id, catalyst_composition_id, percentage, quantity_used 
                FROM catalyst_catalyst_composition 
                WHERE id = %s
            """, (relation_id,))
            
            rel_data = cur.fetchone()
            if not rel_data:
                return False, "Relationship not found"
                
            catalyst_id, composition_id, old_percentage, old_quantity = rel_data
            
            # Check if composition has enough quantity
            cur.execute("SELECT quantity FROM catalyst_composition WHERE id = %s", (composition_id,))
            result = cur.fetchone()
            total_quantity = float(result[0])
            
            # Calculate current used quantity (excluding this relationship)
            cur.execute("""
                SELECT COALESCE(SUM(quantity_used), 0) 
                FROM catalyst_catalyst_composition 
                WHERE catalyst_composition_id = %s AND id != %s
            """, (composition_id, relation_id))
            result = cur.fetchone()
            current_used = float(result[0]) if result and result[0] else 0
            
            available_quantity = total_quantity - current_used
            if available_quantity < quantity_used:
                return False, f"Not enough quantity available. Available: {available_quantity}, Requested: {quantity_used}"
            
            # Calculate new total percentage
            current_total = get_total_percentage_for_catalyst(catalyst_id)
            new_total = current_total - old_percentage + percentage
            
            if new_total > 1:
                return False, f"Total percentage would exceed 100%. Current total without this composition: {(current_total-old_percentage)*100:.2f}%, Trying to set: {percentage*100:.2f}%, Maximum allowed: {(1-(current_total-old_percentage))*100:.2f}%"
            
            # Update relationship
            cur.execute("""
                UPDATE catalyst_catalyst_composition 
                SET percentage = %s, quantity_used = %s 
                WHERE id = %s
            """, (percentage, quantity_used, relation_id))
            
            conn.commit()
            return True, f"Catalyst composition updated successfully. New total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error updating catalyst composition: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def remove_composition_from_catalyst(relation_id):
    """
    Remove a composition from a catalyst
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return False, "Cannot connect to database"
    
    try:
        with conn.cursor() as cur:
            # Check if relationship exists
            cur.execute("""
                SELECT catalyst_id FROM catalyst_catalyst_composition 
                WHERE id = %s
            """, (relation_id,))
            result = cur.fetchone()
            if not result:
                return False, "Relationship not found"
                
            catalyst_id = result[0]
            
            # Delete relationship
            cur.execute("DELETE FROM catalyst_catalyst_composition WHERE id = %s", (relation_id,))
            conn.commit()
            
            # Calculate new total
            new_total = get_total_percentage_for_catalyst(catalyst_id)
            
            return True, f"Composition removed from catalyst successfully. Remaining total: {new_total*100:.2f}%"
    except Exception as e:
        print(f"❌ Error removing composition from catalyst: {e}")
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def get_catalyst_with_compositions(catalyst_id):
    """
    Get catalyst details with all its compositions
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            # Get catalyst information
            cur.execute("""
                SELECT catalyst_id, catalyst_name, provider, created_at 
                FROM catalyst 
                WHERE catalyst_id = %s
            """, (catalyst_id,))
            
            catalyst_data = cur.fetchone()
            if not catalyst_data:
                return None
                
            catalyst = {
                "catalyst_id": catalyst_data[0],
                "catalyst_name": catalyst_data[1],
                "provider": catalyst_data[2],
                "created_at": catalyst_data[3],
                "compositions": []
            }
            
            # Get compositions
            compositions = get_compositions_by_catalyst_id(catalyst_id)
            print(compositions, "compositions", flush=True)
            catalyst["compositions"] = compositions
            
            # Calculate total percentage
            total_percentage = get_total_percentage_for_catalyst(catalyst_id)
            catalyst["total_percentage"] = total_percentage
            
            return catalyst
    except Exception as e:
        print(f"❌ Error getting catalyst with compositions: {e}")
        return None
    finally:
        conn.close()

def get_relation_by_id(relation_id):
    """
    Get a specific catalyst-composition relationship by ID
    """
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cc.id, cc.catalyst_id, c.id as composition_id, c.name, 
                       cc.percentage, cc.quantity_used, c.quantity, cc.created_at
                FROM catalyst_catalyst_composition cc
                JOIN catalyst_composition c ON cc.catalyst_composition_id = c.id
                WHERE cc.id = %s
            """, (relation_id,))
            rel = cur.fetchone()
            
            if rel:
                return {
                    "id": rel[0],
                    "catalyst_id": rel[1],
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
                SELECT id, name, quantity, surface_area, acidity, support_type, provider, impurity, proportion
                FROM catalyst_composition 
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
                    FROM catalyst_catalyst_composition 
                    WHERE catalyst_composition_id = %s
                """, (comp[0],))
                usage_data = cur.fetchone()
                used_quantity = float(usage_data[0]) if usage_data and usage_data[0] else 0
                available_quantity = float(comp[2]) - used_quantity
                
                result.append({
                    "id": comp[0],
                    "name": comp[1],
                    "quantity": available_quantity,
                    "total_quantity": comp[2],
                    "surface_area": comp[3],
                    "acidity": comp[4],
                    "support_type": comp[5],
                    "provider": comp[6],
                    "impurity": comp[7],
                    "proportion": comp[8]
                })
            
            return result
    except Exception as e:
        print(f"❌ Error searching compositions by name: {e}")
        return []
    finally:
        conn.close()
