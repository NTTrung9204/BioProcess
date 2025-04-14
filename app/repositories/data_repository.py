import pandas as pd
import numpy as np
import psycopg2
from app.config import PostgresConfig
from app.repositories.database import get_db_connection

def init_timescale_database():
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
            data_copy = data.copy()
            keys_to_process = list(data_copy.keys())

            for key in keys_to_process:
                if key in PostgresConfig.SENSOR_MAPPINGS:
                    data[PostgresConfig.SENSOR_MAPPINGS[key]] = data[key]
                    del data[key]
                if key in PostgresConfig.SENSOR_MAPPINGS_POWER_BI:
                    data[PostgresConfig.SENSOR_MAPPINGS_POWER_BI[key]] = data[key]
                    del data[key]

            valid_columns = set(
                [
                    col.split()[0].replace('"', "")
                    for col in PostgresConfig.DATABASE_PILOT_TABLE_COLUMNS
                ]
            )
            print(f"Valid columns: {valid_columns}", flush=True)
            validated_data = {}
            for col in valid_columns:
                validated_data[col] = data.get(col, None)

            validated_data = {
                k: v for k, v in validated_data.items() if k in valid_columns
            }

        elif table == PostgresConfig.TABLE_NAME_FTIR:
            valid_columns = set(
                [
                    col.split()[0].replace('"', "")
                    for col in PostgresConfig.DATABASE_FTIR_TABLE_COLUMNS
                ]
            )

            validated_data = {}
            for col in valid_columns:
                validated_data[col] = data.get(col, None)

            validated_data = {
                k: v for k, v in validated_data.items() if k in valid_columns
            }
        else:
            print(f"❌ Unknown table: {table}", flush=True)
            return

        print(f"Validated data: {validated_data}", flush=True)
        for key, value in validated_data.items():
            if hasattr(value, "dtype") and hasattr(value, "item"):
                try:
                    validated_data[key] = value.item()
                except (ValueError, AttributeError):
                    validated_data[key] = str(value)
            elif isinstance(value, (np.ndarray, list)):
                validated_data[key] = str(value)

        columns = ", ".join(f'"{col}"' for col in validated_data.keys())
        values = ", ".join(["%s"] * len(validated_data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"

        cur.execute(query, tuple(validated_data.values()))
        conn.commit()
        print(f"✅ Data has been saved to the table {table}.", flush=True)

    except Exception as e:
        print(f"❌ Error when inserting data into table {table}: {e}", flush=True)

    finally:
        if "cur" in locals() and cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def insert_bulk_to_db(table, df):
    if df.empty:
        print("❌ No data to insert into the database.", flush=True)
        return

    conn = get_db_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        data_list = df.to_dict(orient="records")

        columns = data_list[0].keys()

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

    raman_cols = [
        str(col)
        for col in range(
            int(PostgresConfig.FTIR_MIN_COLUMN), int(PostgresConfig.FTIR_MAX_COLUMN) + 1
        )
    ]

    raman_cols_str = ", ".join([f'"{col}"' for col in raman_cols])
    query = f"SELECT {raman_cols_str} FROM {PostgresConfig.TABLE_NAME_FTIR} WHERE {PostgresConfig.RUN_ID} = %s;"

    cursor.execute(query, (batch_id,))
    data = cursor.fetchall()

    column_names = [desc[0] for desc in cursor.description]

    cursor.close()
    conn.close()

    df = pd.DataFrame(data, columns=column_names)
    return df


def fetch_new_data_by_batch_id(batch_id, last_timestamp=None):
    conn = psycopg2.connect(**PostgresConfig.POSTGRES_CONFIG)
    cursor = conn.cursor()

    raman_cols = [
        str(col)
        for col in range(
            int(PostgresConfig.FTIR_MIN_COLUMN), int(PostgresConfig.FTIR_MAX_COLUMN) + 1
        )
    ]
    raman_cols_str = ", ".join([f'"{col}"' for col in raman_cols])

    if last_timestamp:
        query = f"""
        SELECT {raman_cols_str}, timestamp, {PostgresConfig.PREDICTED_OIL_CONCENTRATION}
        FROM {PostgresConfig.TABLE_NAME_FTIR} 
        WHERE {PostgresConfig.RUN_ID} = %s AND timestamp > %s
        ORDER BY timestamp
        """
        cursor.execute(query, (batch_id, last_timestamp))
    else:
        query = f"""
        SELECT {raman_cols_str}, timestamp, {PostgresConfig.PREDICTED_OIL_CONCENTRATION}
        FROM {PostgresConfig.TABLE_NAME_FTIR} 
        WHERE {PostgresConfig.RUN_ID} = %s
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

    raman_cols = [
        str(col)
        for col in range(
            int(PostgresConfig.FTIR_MIN_COLUMN), int(PostgresConfig.FTIR_MAX_COLUMN) + 1
        )
    ]
    raman_cols_str = ", ".join([f'"{col}"' for col in raman_cols])

    query = f"""
    SELECT {raman_cols_str}, timestamp 
    FROM {PostgresConfig.TABLE_NAME_FTIR} 
    WHERE {PostgresConfig.RUN_ID} = %s AND timestamp BETWEEN %s AND %s
    ORDER BY timestamp
    """
    cursor.execute(query, (batch_id, start_time, end_time))

    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]

    cursor.close()
    conn.close()

    df = pd.DataFrame(data, columns=column_names)
    return df
