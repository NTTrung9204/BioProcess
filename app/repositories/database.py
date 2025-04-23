import psycopg2
from app.config import PostgresConfig

def query_database(custom_query):
    """
    Execute a custom SQL query and return the results
    """
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**PostgresConfig.POSTGRES_CONFIG)
        cursor = conn.cursor()
        cursor.execute(custom_query)
        column_names = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        
        result = [dict(zip(column_names, row)) for row in data]
        return result, column_names
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close() 

def get_db_connection(config=PostgresConfig.POSTGRES_CONFIG):
    """
    Create and return a database connection
    """
    try:
        return psycopg2.connect(**config)
    except Exception as e:
        print(f"❌ Database connection error: {e}", flush=True)
        return None
