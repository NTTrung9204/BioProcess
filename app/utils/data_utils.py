import requests
from app.config import PostgresConfig, RouterConfig

def get_producer_status():
    """
    Check if the producer service is running by querying the API
    """
    try:
        response = requests.get(
            f"{RouterConfig.BASE_URL}/{RouterConfig.ROUTE_PRODUCER_STATUS}"
        )
        return response.json().get("producer_running", True)
    except:
        return True

def map_record(record):
    new_record = {}
    for key, value in record.items():
        new_key = PostgresConfig.SENSOR_MAPPINGS.get(key, key)
        new_record[new_key] = value
    return new_record 