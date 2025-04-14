import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from app.utils import load_ml_model, load_plsr_model, predict_ml_model, predict_raman
from app.config import PathConfig, PostgresConfig, HostConfig, KeyConfig, RouterConfig
from app.repositories import insert_bulk_to_db

def upload_csv_service(file, form_data):
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(PathConfig.UPLOAD_FOLDER, f"{timestamp}.csv")
    
    file.save(file_path)
    
    df = pd.read_csv(file_path)

    df_timestamp = df[PostgresConfig.TIMESTAMP].copy()
    # count columns
    num_columns = len(df.columns)

    if num_columns < 50:
        ml_model = load_ml_model()

        MAPPED_COLUMNS = PostgresConfig.SENSOR_MAPPINGS
        MAPPED_COLUMNS_POWER_BI = PostgresConfig.SENSOR_MAPPINGS_POWER_BI

        df = df.rename(columns=MAPPED_COLUMNS)
        df = df.rename(columns=MAPPED_COLUMNS_POWER_BI)

        df = df[list(MAPPED_COLUMNS.values()) + list(MAPPED_COLUMNS_POWER_BI.values())]

        df_features = df[PostgresConfig.PILOT_COLUMNS].astype(np.float32)

        predictions = predict_ml_model(df_features, ml_model)
        
        df[PostgresConfig.PREDICTED_OIL] = predictions.astype(float)
    else:
        plrs_model = load_plsr_model()

        df = df[PostgresConfig.FTIR_COLUMNS]

        df_features = df[PostgresConfig.FTIR_COLUMNS].astype(np.float32)

        predictions = predict_raman(df_features, plrs_model)

        df[PostgresConfig.PREDICTED_OIL_CONCENTRATION] = predictions.astype(float)
        
    df[PostgresConfig.TIMESTAMP] = df_timestamp

    for key, value in form_data.items():
        df[key] = value

    
    if num_columns < 50:
        insert_bulk_to_db(PostgresConfig.TABLE_NAME_PILOT, df)
    else:
        insert_bulk_to_db(PostgresConfig.TABLE_NAME_FTIR, df)

    if HostConfig.HOST_TARGET:
        send_csv_to_another_vm(file_path, form_data)

def send_csv_to_another_vm(file_path, form_data):
    try:
        files = {'file': open(file_path, 'rb')}
        
        data = {**form_data}
        
        if 'source_vm' not in data:
            data['source_vm'] = HostConfig.HOST_IP
        
        headers = {
            'Authorization': f'Bearer {KeyConfig.API_KEY}'
        }
        
        response = requests.post(
            f"http://{HostConfig.HOST_TARGET}/{RouterConfig.ROUTE_RECEIVE_CSV}", 
            files=files, 
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ File {file_path} successfully sent to remote VM")
            return True
        else:
            print(f"❌ Failed to send file to remote VM. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending file to remote VM: {e}")
        return False 