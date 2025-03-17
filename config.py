import os

class HostConfig:
    HOST_IP = os.getenv("HOST_IP", "localhost")
    HOST_PORT = os.getenv("HOST_PORT", "5000")

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

class PathConfig:
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MODEL_FOLDER = os.getenv("MODEL_FOLDER", "model")
    XGBOOST_MODEL = os.getenv("XGBOOST_MODEL", "xgboost_model.json")
    PLS_MODEL = os.getenv("PLS_MODEL", "pls_model.joblib")
    SCALER_X = os.getenv("SCALER_X", "scaler_x.joblib")
    SCALER_Y = os.getenv("SCALER_Y", "scaler_y.joblib")

class PostgresConfig:
    POSTGRES_CONFIG = {
        "dbname": os.getenv("POSTGRES_DB", "sensor_db"),
        "user": os.getenv("POSTGRES_USER", "user"),
        "password": os.getenv("POSTGRES_PASSWORD", "password"),
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    POSTGRES_CONFIG_TEMP = {
        "dbname": "temp_db",
        "user": os.getenv("POSTGRES_USER", "user"),
        "password": os.getenv("POSTGRES_PASSWORD", "password"),
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    TABLE_NAME_OPERATION = os.getenv("TABLE_NAME_OPERATION", "operation")
    TABLE_NAME_RAMAN = os.getenv("TABLE_NAME_RAMAN", "raman")
    TABLE_NAME_TEMP = os.getenv("TABLE_NAME_TEMP", "temp_operation")

    PEN_COL = os.getenv("PEN_COL", "Penicillin concentration(P:g/L)")
    VV_COL = os.getenv("VV_COL", "Vessel Volume(V:L)")
    WTFD_COL = os.getenv("WTFD_COL", "Water for injection/dilution(Fw:L/h)")
    ARATE_COL = os.getenv("ARATE_COL", "Aeration rate(Fg:L/h)")
    SFR_COL = os.getenv("SFR_COL", "Sugar feed rate(Fs:L/h)")
    DO_COL = os.getenv("DO_COL", "Dissolved oxygen concentration(DO2:mg/L)")
    TEM_COL = os.getenv("TEM_COL", "Temperature(T:K)")
    TIME_COL = os.getenv("TIME_COL", "Time (h)")
    OUR_COL = os.getenv("OUR_COL", "Oxygen Uptake Rate(OUR:(g min^{-1}))")

    FEATURES = [
        TEM_COL,
        DO_COL,
        SFR_COL,
        ARATE_COL,
        WTFD_COL,
        VV_COL,
        OUR_COL,
        TIME_COL,
    ]

    TEMPERATURE = os.getenv("TEMPERATURE", "temperature")
    DISSOLVED_OXYGEN = os.getenv("DISSOLVED_OXYGEN", "dissolved_oxygen")
    SUGAR_FEED_RATE = os.getenv("SUGAR_FEED_RATE", "sugar_feed_rate")
    AERATION_RATE = os.getenv("AERATION_RATE", "aeration_rate")
    WATER_INJECTION = os.getenv("WATER_INJECTION", "water_injection")
    VESSEL_VOLUME = os.getenv("VESSEL_VOLUME", "vessel_volume")
    OXYGEN_UPTAKE = os.getenv("OXYGEN_UPTAKE", "oxygen_uptake")
    TIME_H = os.getenv("TIME_H", "time_h")

    TIMESTAMP = os.getenv("TIMESTAMP", "timestamp")
    SCAN = os.getenv("SCAN", "scan")
    PENICILLIN = os.getenv("PENICILLIN", "penicillin")
    PREDICTION = os.getenv("PREDICTION", "prediction")
    CUST = os.getenv("CUST", "cust")
    PROJECT_ID = os.getenv("PROJECT_ID", "project_id")
    BATCH_ID = os.getenv("BATCH_ID", "batchid")

    COLUMN_MAPPING = {
        PEN_COL: PENICILLIN,
        VV_COL: VESSEL_VOLUME,
        WTFD_COL: WATER_INJECTION,
        ARATE_COL: AERATION_RATE,
        SFR_COL: SUGAR_FEED_RATE,
        DO_COL: DISSOLVED_OXYGEN,
        TEM_COL: TEMPERATURE,
        TIME_COL: TIME_H,
        OUR_COL: OXYGEN_UPTAKE,
    }

    OPERATION_COLUMNS = [
        TEMPERATURE,
        DISSOLVED_OXYGEN,
        SUGAR_FEED_RATE,
        AERATION_RATE,
        WATER_INJECTION,
        VESSEL_VOLUME,
        OXYGEN_UPTAKE,
        TIME_H,
    ]

    RAMAN_COLUMNS = [
        str(i)
        for i in range(
            int(os.getenv("RAMAN_MAX_COLUMN", "1350")),
            int(os.getenv("RAMAN_MIN_COLUMN", "1099")),
            -1,
        )
    ]

    DATABASE_OPERATION_TABLE_COLUMNS = [
        f"{TIMESTAMP} TIMESTAMP UNIQUE DEFAULT NULL",
        f"{SCAN} INTEGER",
        f"{PENICILLIN} FLOAT DEFAULT NULL",
        f"{PREDICTION} FLOAT DEFAULT NULL",
        f"{TIME_H} FLOAT DEFAULT NULL",
        f"{DISSOLVED_OXYGEN} FLOAT DEFAULT NULL",
        f"{SUGAR_FEED_RATE} FLOAT DEFAULT NULL",
        f"{AERATION_RATE} FLOAT DEFAULT NULL",
        f"{WATER_INJECTION} FLOAT DEFAULT NULL",
        f"{VESSEL_VOLUME} FLOAT DEFAULT NULL",
        f"{OXYGEN_UPTAKE} FLOAT DEFAULT NULL",
        f"{TEMPERATURE} FLOAT DEFAULT NULL",
        f"{CUST} TEXT DEFAULT NULL",
        f"{PROJECT_ID} TEXT DEFAULT NULL",
        f"{BATCH_ID} TEXT DEFAULT NULL",
    ]

    DATABASE_RAMAN_TABLE_COLUMNS = [
        f"{TIMESTAMP} TIMESTAMP UNIQUE",
        f"{SCAN} INTEGER",
        f"{PREDICTION} FLOAT",
    ] + [f'"{col}" FLOAT' for col in RAMAN_COLUMNS]

class KafkaConfig:
    KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

    KAFKA_TOPIC_OPERATION = os.getenv("KAFKA_TOPIC_OPERATION", "operation_data")
    KAFKA_TOPIC_RAMAN = os.getenv("KAFKA_TOPIC_RAMAN", "raman_data")

    TOPICS = [
        KAFKA_TOPIC_OPERATION,
        KAFKA_TOPIC_RAMAN,
    ]
