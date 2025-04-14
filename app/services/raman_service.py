import base64
import io
from datetime import datetime
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from app.repositories import fetch_raman_data
from app.config import PostgresConfig

def generate_plot(spectrum_df):
    raman_cols = [str(col) for col in range(int(PostgresConfig.FTIR_MIN_COLUMN), int(PostgresConfig.FTIR_MAX_COLUMN) + 1)]
    spectrum_df = spectrum_df[raman_cols]

    plt.figure(figsize=(10, 6))
    
    spectrum_df.columns = [int(col) for col in spectrum_df.columns]
    spectrum_df = spectrum_df.reindex(sorted(spectrum_df.columns, reverse=True), axis=1)
    
    x_values = np.linspace(PostgresConfig.FTIR_MIN_COLUMN, int(PostgresConfig.FTIR_MAX_COLUMN), num=spectrum_df.shape[1])
    
    for i in range(spectrum_df.shape[0]):
        plt.plot(x_values, spectrum_df.iloc[i])
    
    plt.title('Experimental Raman Spectra')
    plt.xlabel('Wavenumber (cm$^{-1}$)')
    plt.ylabel('Intensity (a.u.)')
    plt.grid(True)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_data

def raman_plot_in_range(batch_id, start_time, end_time):
    start_time = datetime.fromisoformat(start_time)
    end_time = datetime.fromisoformat(end_time)

    df = fetch_raman_data(batch_id, start_time, end_time)
    error = None

    if df.empty:
        error = 'No data found for the specified parameters'
        return df, None, error

    plot_image = generate_plot(df)

    return df, plot_image, None 