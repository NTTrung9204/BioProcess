import psycopg2
from config import PostgresConfig

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
        print(f"❌ Database connection error: {e}")
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

        if table == PostgresConfig.TABLE_NAME_OPERATION:
            cur.execute(
                f"""
                INSERT INTO {PostgresConfig.TABLE_NAME_OPERATION} (
                    {PostgresConfig.TIMESTAMP}, {PostgresConfig.SCAN}, {PostgresConfig.PENICILLIN}, 
                    {PostgresConfig.PREDICTION}, {PostgresConfig.TIME_H}, {PostgresConfig.DISSOLVED_OXYGEN}, 
                    {PostgresConfig.SUGAR_FEED_RATE}, {PostgresConfig.AERATION_RATE}, {PostgresConfig.WATER_INJECTION}, 
                    {PostgresConfig.VESSEL_VOLUME}, {PostgresConfig.OXYGEN_UPTAKE}, {PostgresConfig.TEMPERATURE}, 
                    {PostgresConfig.CUST}, {PostgresConfig.PROJECT_ID}, {PostgresConfig.BATCH_ID}
                ) VALUES ({", ".join(["%s"] * 15)})
                """,
                (
                    data[PostgresConfig.TIMESTAMP],
                    data[PostgresConfig.SCAN],
                    data[PostgresConfig.PENICILLIN],
                    data[PostgresConfig.PREDICTION],
                    data[PostgresConfig.TIME_H],
                    data[PostgresConfig.DISSOLVED_OXYGEN],
                    data[PostgresConfig.SUGAR_FEED_RATE],
                    data[PostgresConfig.AERATION_RATE],
                    data[PostgresConfig.WATER_INJECTION],
                    data[PostgresConfig.VESSEL_VOLUME],
                    data[PostgresConfig.OXYGEN_UPTAKE],
                    data[PostgresConfig.TEMPERATURE],
                    data[PostgresConfig.CUST],
                    data[PostgresConfig.PROJECT_ID],
                    data[PostgresConfig.BATCH_ID],
                ),
            )

        elif table == PostgresConfig.TABLE_NAME_RAMAN:
            columns = ", ".join(f'"{col}"' for col in data.keys())
            values = ", ".join(["%s"] * len(data))
            query = f"INSERT INTO {PostgresConfig.TABLE_NAME_RAMAN} ({columns}) VALUES ({values})"

            cur.execute(query, tuple(data.values()))

        conn.commit()
        print(f"✅ Data has been saved to the table {table}.")

    except Exception as e:
        print(f"❌ Error when inserting data into table {table}: {e}")

    finally:
        cur.close()
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

def insert_bulk_to_db(table, data_list):
    if not data_list:
        print("❌ No data to insert into the database.")
        return

    conn = get_db_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        columns = data_list[0].keys()
        
        column_names = ", ".join(f'"{col}"' for col in columns)
        values_placeholder = ", ".join(["%s"] * len(columns))

        query = f"INSERT INTO {table} ({column_names}) VALUES ({values_placeholder})"

        values = [tuple(data[col] for col in columns) for data in data_list]

        cur.executemany(query, values)

        conn.commit()
        print(f"✅ {len(data_list)} rows inserted into table {table}.")

    except Exception as e:
        print(f"❌ Error when bulk inserting data into {table}: {e}")

    finally:
        cur.close()
        conn.close()