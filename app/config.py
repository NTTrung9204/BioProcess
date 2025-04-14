import json
import os


class HostConfig:
    HOST_IP = os.getenv("HOST_IP", "localhost")
    HOST_PORT = os.getenv("HOST_PORT", "5000")
    HOST_TARGET = os.getenv("HOST_TARGET", None)

class RouterConfig:
    BASE_URL = f"http://{HostConfig.HOST_IP}:{HostConfig.HOST_PORT}"

    ROUTE_PRODUCER_STATUS = os.getenv("ROUTE_PRODUCER_STATUS", "status")
    ROUTE_UPLOAD = os.getenv("ROUTE_UPLOAD", "upload")
    ROUTE_TOGGLE_PRODUCER = os.getenv("ROUTE_TOGGLE_PRODUCER", "toggle_producer")
    ROUTE_BAYESIAN_OPTIMAZATION = os.getenv(
        "ROUTE_BAYESIAN_OPTIMAZATION", "bayesian_optimazation"
    )
    ROUTE_CONTOUR_PLOT = os.getenv("ROUTE_CONTOUR_PLOT", "contour_plot")
    ROUTE_QUERY = os.getenv("ROUTE_QUERY", "query")
    ROUTE_RECEIVE_CSV = os.getenv("ROUTE_RECEIVE_CSV", "receive_csv")


class PathConfig:
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MODEL_FOLDER = os.getenv("MODEL_FOLDER", "model")
    MODEL_1 = os.getenv("MODEL_1", "svm_model.pkl")
    MODEL_1_SCALER_X = os.getenv("MODEL_1_SCALER_X", "svm_model.pkl")
    MODEL_1_SCALER_Y = os.getenv("MODEL_1_SCALER_Y", "svm_model.pkl")
    MODEL_2 = os.getenv("MODEL_2", "svm_model.pkl")
    MODEL_2_SCALER_X = os.getenv("MODEL_2_SCALER_X", "svm_model.pkl")
    MODEL_2_SCALER_Y = os.getenv("MODEL_2_SCALER_Y", "svm_model.pkl")


class PostgresConfig:
    POSTGRES_CONFIG = {
        "dbname": os.getenv("POSTGRES_DB", "sensor_db"),
        "user": os.getenv("POSTGRES_USER", "user"),
        "password": os.getenv("POSTGRES_PASSWORD", "password"),
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    POSTGRES_CONFIG_TEMP = {
        "dbname": os.getenv("POSTGRES_DB", "sensor_db"),
        "user": os.getenv("POSTGRES_USER", "user"),
        "password": os.getenv("POSTGRES_PASSWORD", "password"),
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    TABLE_NAME_PILOT = os.getenv("TABLE_NAME_PILOT", "pilot")
    TABLE_NAME_FTIR = os.getenv("TABLE_NAME_FTIR", "ftir")
    TABLE_NAME_TEMP = os.getenv("TABLE_NAME_TEMP", "temp_pilot")

    TIMESTAMP = os.getenv("TIMESTAMP", "timestamp")
    SCAN = os.getenv("SCAN", "scan")
    CUST = os.getenv("CUST", "cust")
    SAMPLE_ID = os.getenv("SAMPLE_ID", "sample_id")
    TEST_CAMPAING_ID = os.getenv("TEST_CAMPAING_ID", "test_campaing_id")
    RUN_ID = os.getenv("RUN_ID", "run_id")

    PREDICTED_OIL = os.getenv("PREDICTED_OIL", "predicted_oil_yield")
    PREDICTED_OIL_CONCENTRATION = os.getenv(
        "PREDICTED_OIL_CONCENTRATION", "predicted_oil_concentration"
    )

    FTIR_MAX_COLUMN = int(os.getenv("FTIR_MAX_COLUMN", "1200"))
    FTIR_MIN_COLUMN = int(os.getenv("FTIR_MIN_COLUMN", "199"))

    FTIR_COLUMNS = [
        str(i)
        for i in range(
            FTIR_MAX_COLUMN,
            FTIR_MIN_COLUMN - 1,
            -1,
        )
    ]

    SENSOR_DEFINITIONS_JSON = os.getenv("SENSOR_COLUMNS_ML_MODEL", "{}")
    SENSOR_DEFINITIONS_JSON_POWER_BI = os.getenv("SENSOR_COLUMNS_ML_POWER_BI", "{}")

    try:
        _sensor_data = json.loads(SENSOR_DEFINITIONS_JSON)

        SENSOR_MAPPINGS = {}

        for display_name, value_string in _sensor_data.items():
            parts = value_string.split(":")
            column_name = parts[0]
            SENSOR_MAPPINGS[display_name] = column_name

    except json.JSONDecodeError:
        print("Error parsing JSON from environment variable SENSOR_COLUMNS", flush=True)
        SENSOR_MAPPINGS = {}

    try:
        SENSOR_MAPPINGS_POWER_BI = json.loads(SENSOR_DEFINITIONS_JSON_POWER_BI)

    except json.JSONDecodeError:
        print("Error parsing JSON from environment variable SENSOR_COLUMNS_ML_POWER_BI", flush=True)
        SENSOR_MAPPINGS_POWER_BI = {}


    FEATURES = list(SENSOR_MAPPINGS.keys())
    PILOT_COLUMNS = list(SENSOR_MAPPINGS.values())

    _COMMON_COLUMNS = [
        f"{TIMESTAMP} TIMESTAMP UNIQUE",
        f"{SCAN} INTEGER DEFAULT 0",
        f"{CUST} TEXT DEFAULT NULL",
        f"{SAMPLE_ID} TEXT DEFAULT NULL",
        f"{TEST_CAMPAING_ID} TEXT DEFAULT NULL",
        f"{RUN_ID} TEXT DEFAULT NULL",
    ]
    
    DATABASE_PILOT_TABLE_COLUMNS = _COMMON_COLUMNS.copy()
    DATABASE_PILOT_TABLE_COLUMNS.extend(
        [f'"{PREDICTED_OIL}" FLOAT DEFAULT 0']
        + [f'"{column_name}" FLOAT DEFAULT NULL' for column_name in list(SENSOR_MAPPINGS_POWER_BI.values())]
        + [f'"{column_name}" FLOAT DEFAULT NULL' for column_name in PILOT_COLUMNS]
    )

    DATABASE_FTIR_TABLE_COLUMNS = _COMMON_COLUMNS.copy()
    DATABASE_FTIR_TABLE_COLUMNS.extend(
        [f'"{PREDICTED_OIL_CONCENTRATION}" FLOAT DEFAULT 0'] + [f'"{col}" FLOAT DEFAULT NULL' for col in FTIR_COLUMNS]
    )


class KafkaConfig: 
    KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
    KAFKA_TOPIC_PILOT = os.getenv("KAFKA_TOPIC_PILOT", "data_1")
    KAFKA_TOPIC_FTIR = os.getenv("KAFKA_TOPIC_FTIR", "data_2")

    TOPICS = [
        KAFKA_TOPIC_PILOT,
        KAFKA_TOPIC_FTIR,
    ]


class UserConfig:
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "trungdeptrai")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "goodmorning")
    USERNAME_2 = os.getenv("USERNAME_2", "abcyxz")
    PASSWORD_2 = os.getenv("PASSWORD_2", "abcyxz")
    USERNAME_3 = os.getenv("USERNAME_3", "abcyxz")
    PASSWORD_3 = os.getenv("PASSWORD_3", "abcyxz")
    UserDBInstance = {
        ADMIN_USERNAME: ADMIN_PASSWORD,
        USERNAME_2: PASSWORD_2,
        USERNAME_3: PASSWORD_3,
    }


class KeyConfig:
    API_KEY = os.getenv("API_KEY", "")
    VERIFIED_API_KEY = os.getenv("VERIFIED_API_KEY", "")


class RunningConfig:
    NUM_ROWS_ConPLOT = int(os.getenv("NUM_ROWS_ConPLOT", "4"))
    NUM_COLs_ConPLOT = int(os.getenv("NUM_COLs_ConPLOT", "4"))

    NUM_TRIALS_BO = int(os.getenv("NUM_TRIALS_BO", "1000"))
    LEVEL_BO_DOE = int(os.getenv("LEVEL_BO_DOE", "4"))
