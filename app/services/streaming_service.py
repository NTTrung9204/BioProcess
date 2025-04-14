import gc
import time
import pandas as pd
from app.repositories import fetch_new_data_by_batch_id
from app.config import PostgresConfig
from app.services.raman_service import generate_plot

def start_streaming(batch_id, session_id, active_streams, socketio):
    previous_data = {'dataframe': None, 'last_timestamp': None}
    
    try:
        while session_id in active_streams and active_streams[session_id]:
            try:
                new_df = fetch_new_data_by_batch_id(batch_id, previous_data.get('last_timestamp'))
                
                if not new_df.empty:
                    if previous_data.get('dataframe') is not None:
                        combined_df = pd.concat([previous_data['dataframe'], new_df], ignore_index=True)
                    else:
                        combined_df = new_df

                    if len(combined_df) > 300:
                        combined_df = combined_df.sort_values('timestamp', ascending=False).head(300).reset_index(drop=True)
                    
                    last_timestamp = combined_df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
                    
                    previous_data['dataframe'] = combined_df
                    previous_data['last_timestamp'] = last_timestamp
                    
                    img_data = generate_plot(combined_df)
                    sample_count = len(combined_df)
                    
                    sorted_df = combined_df.sort_values('timestamp')
                    
                    timestamps = sorted_df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist()
                    concentrations = sorted_df[PostgresConfig.PREDICTED_OIL_CONCENTRATION].tolist()
                    
                    socketio.emit('update_data', {
                        'image': img_data, 
                        'count': sample_count,
                        'timestamp': previous_data['last_timestamp'],
                        'timestamps': timestamps,
                        'concentrations': concentrations
                    }, room=session_id)
                elif previous_data.get('dataframe') is not None:
                    img_data = generate_plot(previous_data['dataframe'])
                    sample_count = len(previous_data['dataframe'])
                    
                    sorted_df = previous_data['dataframe'].sort_values('timestamp')
                    timestamps = sorted_df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist()
                    concentrations = sorted_df[PostgresConfig.PREDICTED_OIL_CONCENTRATION].tolist()
                    
                    socketio.emit('update_data', {
                        'image': img_data, 
                        'count': sample_count,
                        'timestamp': previous_data.get('last_timestamp', 'No new updates'),
                        'timestamps': timestamps,
                        'concentrations': concentrations
                    }, room=session_id)
                else:
                    socketio.emit('no_data', {'message': f'No data found for batch ID: {batch_id}'}, room=session_id)
            
            except Exception as e:
                socketio.emit('error', {'message': str(e)}, room=session_id)
            
            time.sleep(5)

    finally:
        if 'dataframe' in previous_data:
            previous_data['dataframe'] = None
        previous_data.clear()
        
        gc.collect() 