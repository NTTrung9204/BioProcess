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

def create_table(table_name, columns, config=PostgresConfig.POSTGRES_CONFIG):
    """
    Create a table in the database if it doesn't exist
    """
    conn = get_db_connection(config)
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            column_definitions = ",\n        ".join(columns)
            query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    {column_definitions}
                );
            """
            cur.execute(query)
            conn.commit()
            print(f"✅ Table '{table_name}' created successfully.")
    except Exception as e:
        print(f"❌ Error when creating table '{table_name}': {e}")
    finally:
        conn.close()

def init_timescale_database():
    """
    Initialize the TimescaleDB database with required tables and extensions
    """
    print("🚀 Initializing TimescaleDB database...")
    
    conn = get_db_connection(PostgresConfig.POSTGRES_CONFIG)
    if conn is None:
        print("❌ Cannot connect to main database")
        return False
    
    try:
        conn.autocommit = True
        
        with conn.cursor() as cur:
            try:
                cur.execute("CREATE DATABASE temp_db;")
                print("✅ Database temp_db created")
            except Exception as e:
                if "already exists" in str(e):
                    print("ℹ️ Database temp_db already exists")
                else:
                    print(f"❌ Error when creating temp_db: {e}")
            
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                print("✅ TimescaleDB extension created")
            except Exception as e:
                print(f"❌ Error when creating TimescaleDB extension: {e}")

            common_cols = [
                f"{PostgresConfig.TIMESTAMP} TIMESTAMP NOT NULL",
                f"{PostgresConfig.SCAN} INTEGER DEFAULT 0",
                f"{PostgresConfig.CUST} TEXT DEFAULT NULL",
                f"{PostgresConfig.SAMPLE_ID} TEXT DEFAULT NULL",
                f"{PostgresConfig.TEST_CAMPAING_ID} TEXT DEFAULT NULL",
                f"{PostgresConfig.RUN_ID} TEXT DEFAULT NULL"
            ]
            
            operation_table = PostgresConfig.TABLE_NAME_PILOT
            pred_oil = PostgresConfig.PREDICTED_OIL
            
            sensor_columns = []
            for column_name in PostgresConfig.PILOT_COLUMNS:
                sensor_columns.append(f'"{column_name}" FLOAT DEFAULT NULL')
            
            power_bi_columns = []
            for column_name in PostgresConfig.SENSOR_MAPPINGS_POWER_BI.values():
                power_bi_columns.append(f'"{column_name}" FLOAT DEFAULT NULL')
            
            operation_columns = common_cols + [f'"{pred_oil}" FLOAT DEFAULT 0'] + sensor_columns + power_bi_columns
            operation_columns_sql = ",\n        ".join(operation_columns)
            
            try:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {operation_table} (
                        id SERIAL,
                        {operation_columns_sql},
                        PRIMARY KEY (id, {PostgresConfig.TIMESTAMP})
                    );
                """)
                print(f"✅ Table {operation_table} created")
                
                try:
                    cur.execute(f"SELECT create_hypertable('{operation_table}', '{PostgresConfig.TIMESTAMP}', if_not_exists => TRUE);")
                    print(f"✅ Table {operation_table} converted to hypertable")
                except Exception as e:
                    if "already a hypertable" in str(e):
                        print(f"ℹ️ Table {operation_table} is already a hypertable")
                    else:
                        print(f"❌ Error when converting {operation_table} to hypertable: {e}")
            except Exception as e:
                print(f"❌ Error when creating table {operation_table}: {e}")
            

            raman_table = PostgresConfig.TABLE_NAME_FTIR
            pred_oil_concentration = PostgresConfig.PREDICTED_OIL_CONCENTRATION
            
            raman_columns = common_cols + [f'"{pred_oil_concentration}" FLOAT DEFAULT 0']
            raman_columns_sql = ",\n        ".join(raman_columns)
            
            try:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {raman_table} (
                        id SERIAL,
                        {raman_columns_sql},
                        PRIMARY KEY (id, {PostgresConfig.TIMESTAMP})
                    );
                """)
                print(f"✅ Table {raman_table} created")
                
                ftir_min = PostgresConfig.FTIR_MIN_COLUMN
                ftir_max = PostgresConfig.FTIR_MAX_COLUMN
                
                for i in range(ftir_min, ftir_max + 1):
                    try:
                        cur.execute(f'ALTER TABLE {raman_table} ADD COLUMN IF NOT EXISTS "{i}" FLOAT DEFAULT NULL;')
                    except Exception as e:
                        print(f"❌ Error when adding column {i} to table {raman_table}: {e}")
                
                print(f"✅ Added columns from {ftir_min} to {ftir_max} to table {raman_table}")
                
                try:
                    cur.execute(f"SELECT create_hypertable('{raman_table}', '{PostgresConfig.TIMESTAMP}', if_not_exists => TRUE);")
                    print(f"✅ Table {raman_table} converted to hypertable")
                except Exception as e:
                    if "already a hypertable" in str(e):
                        print(f"ℹ️ Table {raman_table} is already a hypertable")
                    else:
                        print(f"❌ Error when converting {raman_table} to hypertable: {e}")
            except Exception as e:
                print(f"❌ Error when creating table {raman_table}: {e}")
                
            try:
                temp_table = PostgresConfig.TABLE_NAME_TEMP
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {temp_table} (
                        id SERIAL PRIMARY KEY,
                        {operation_columns_sql}
                    );
                """)
                print(f"✅ Table {temp_table} created")
            except Exception as e:
                print(f"❌ Error when creating table {temp_table}: {e}")
                
            print("✅ Database initialization complete!")
            return True
    except Exception as e:
        print(f"❌ Unexpected error during database initialization: {e}")
        return False
    finally:
        conn.close() 