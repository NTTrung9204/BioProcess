import json
import os

class Constants:
    @classmethod
    def get_sensor_data(cls):
        try:
            return json.loads(os.getenv("SENSOR_COLUMNS", "{}"))
        except json.JSONDecodeError:
            return {}
    
    @classmethod
    def get_default_values(cls):
        default_values = {}
        for display_name, value_string in cls.get_sensor_data().items():
            parts = value_string.split(":")
            column_name = parts[0]
            if len(parts) > 1:
                default_values[column_name] = float(parts[1])
        return default_values
    
    @classmethod
    def get_min_values(cls):
        min_values = {}
        for display_name, value_string in cls.get_sensor_data().items():
            parts = value_string.split(":")
            column_name = parts[0]
            if len(parts) > 2:
                min_values[column_name] = float(parts[2])
        return min_values
    
    @classmethod
    def get_max_values(cls):
        max_values = {}
        for display_name, value_string in cls.get_sensor_data().items():
            parts = value_string.split(":")
            column_name = parts[0]
            if len(parts) > 3:
                max_values[column_name] = float(parts[3])
        return max_values