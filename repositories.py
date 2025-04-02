import psycopg2
from config import PostgresConfig
import pandas as pd

def query_database(custom_query):
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
    try:
        return psycopg2.connect(**config)
    except Exception as e:
        print(f"❌ Database connection error: {e}", flush=True)
        return None

def fetch_data():
    conn = psycopg2.connect(**PostgresConfig.POSTGRES_CONFIG_TEMP)
    cursor = conn.cursor()

    query = f"SELECT * FROM {PostgresConfig.TABLE_NAME_TEMP};"
    cursor.execute(query)

    column_names = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(zip(column_names, row)) for row in data]

def insert_data_to_db(table, data, model, scaler_x=None, scaler_y=None):
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()
        
        if table == PostgresConfig.TABLE_NAME_PILOT:
            valid_columns = set([col.split()[0].replace('"', '') for col in PostgresConfig.DATABASE_PILOT_TABLE_COLUMNS])
            
            validated_data = {}
            for col in valid_columns:
                validated_data[col] = data.get(col, None)
                
            validated_data = {k: v for k, v in validated_data.items() if k in valid_columns}
            
        elif table == PostgresConfig.TABLE_NAME_FTIR:
            valid_columns = set([col.split()[0].replace('"', '') for col in PostgresConfig.DATABASE_FTIR_TABLE_COLUMNS])
            
            validated_data = {}
            for col in valid_columns:
                validated_data[col] = data.get(col, None)
                
            validated_data = {k: v for k, v in validated_data.items() if k in valid_columns}
        else:
            print(f"❌ Unknown table: {table}", flush=True)
            return
        
        columns = ", ".join(f'"{col}"' for col in validated_data.keys())
        values = ", ".join(["%s"] * len(validated_data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        
        cur.execute(query, tuple(validated_data.values()))
        conn.commit()
        print(f"✅ Data has been saved to the table {table}.", flush=True)

    except Exception as e:
        print(f"❌ Error when inserting data into table {table}: {e}", flush=True)

    finally:
        if 'cur' in locals() and cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def create_table(table_name, columns, config=PostgresConfig.POSTGRES_CONFIG):
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

def insert_bulk_to_db(table, df):
    # print(f"Insert bulk data to {table}", flush=True)
    if df.empty:
        print("❌ No data to insert into the database.", flush=True)
        return
    
    # print(f"Data to insert: {df['timestamp']}", flush=True)

    conn = get_db_connection()
    if conn is None:
        return
    
    # print(f"Connection to database established.", flush=True)

    try:
        # print(f"Preparing to insert data into {table}", flush=True)
        cur = conn.cursor()

        # print(f"DataFrame shape: {df.shape}", flush=True)
        data_list = df.to_dict(orient='records')

        # print(f"Data to insert: {data_list}", flush=True)
        columns = data_list[0].keys()

        # print(f"Columns: {columns}", flush=True)

        column_names = ", ".join(f'"{col}"' for col in columns)
        values_placeholder = ", ".join(["%s"] * len(columns))

        query = f"INSERT INTO {table} ({column_names}) VALUES ({values_placeholder})"

        values = [tuple(data[col] for col in columns) for data in data_list]

        cur.executemany(query, values)

        conn.commit()
        print(f"✅ {len(data_list)} rows inserted into table {table}.", flush=True)

    except Exception as e:
        print(f"❌ Error when bulk inserting data into {table}: {e}", flush=True)

    finally:
        cur.close()
        conn.close()


def fetch_data_by_batch_id(batch_id):
    conn = psycopg2.connect(**PostgresConfig.POSTGRES_CONFIG)
    cursor = conn.cursor()
    
    raman_cols = [str(col) for col in range(int(PostgresConfig.FTIR_MIN_COLUMN), int(PostgresConfig.FTIR_MAX_COLUMN) + 1)]
    
    raman_cols_str = ", ".join([f'"{col}"' for col in raman_cols])
    query = f"SELECT {raman_cols_str} FROM {PostgresConfig.TABLE_NAME_FTIR} WHERE batchid = %s;"
    
    cursor.execute(query, (batch_id,))
    data = cursor.fetchall()
    
    column_names = [desc[0] for desc in cursor.description]
    
    cursor.close()
    conn.close()
    
    df = pd.DataFrame(data, columns=column_names)
    return df

def fetch_new_data_by_batch_id(batch_id, last_timestamp=None):
    # print(batch_id, last_timestamp, flush=True)
    conn = psycopg2.connect(**PostgresConfig.POSTGRES_CONFIG)
    cursor = conn.cursor()
    
    raman_cols = [str(col) for col in range(int(PostgresConfig.FTIR_MIN_COLUMN), int(PostgresConfig.FTIR_MAX_COLUMN) + 1)]
    raman_cols_str = ", ".join([f'"{col}"' for col in raman_cols])
    
    if last_timestamp:
        query = f"""
        SELECT {raman_cols_str}, timestamp, {PostgresConfig.PREDICTED_OIL_CONCENTRATION}
        FROM {PostgresConfig.TABLE_NAME_FTIR} 
        WHERE {PostgresConfig.SAMPLE_ID} = %s AND timestamp > %s
        ORDER BY timestamp
        """
        cursor.execute(query, (batch_id, last_timestamp))
    else:
        query = f"""
        SELECT {raman_cols_str}, timestamp, {PostgresConfig.PREDICTED_OIL_CONCENTRATION}
        FROM {PostgresConfig.TABLE_NAME_FTIR} 
        WHERE {PostgresConfig.SAMPLE_ID} = %s
        ORDER BY timestamp
        """
        cursor.execute(query, (batch_id,))
    
    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    
    cursor.close()
    conn.close()
    
    df = pd.DataFrame(data, columns=column_names)
    return df

def fetch_raman_data(batch_id, start_time, end_time):
    conn = psycopg2.connect(**PostgresConfig.POSTGRES_CONFIG)
    cursor = conn.cursor()
    
    raman_cols = [str(col) for col in range(int(PostgresConfig.FTIR_MIN_COLUMN), int(PostgresConfig.FTIR_MAX_COLUMN) + 1)]
    raman_cols_str = ", ".join([f'"{col}"' for col in raman_cols])
    
    query = f"""
    SELECT {raman_cols_str}, timestamp 
    FROM {PostgresConfig.TABLE_NAME_FTIR} 
    WHERE {PostgresConfig.SAMPLE_ID} = %s AND timestamp BETWEEN %s AND %s
    ORDER BY timestamp
    """
    cursor.execute(query, (batch_id, start_time, end_time))
    
    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    
    cursor.close()
    conn.close()
    
    df = pd.DataFrame(data, columns=column_names)
    return df