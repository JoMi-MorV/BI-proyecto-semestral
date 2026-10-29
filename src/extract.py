import os
import pandas as pd

def extract_data(file_path: str) -> pd.DataFrame:
    """
    Extrae los registros del archivo plano CSV en Staging (ODS).
    Valida existencia y estructura mínima requerida.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"[ERROR ETL - EXTRACT] Archivo no encontrado en la ruta: {file_path}")
    
    print(f"[EXTRACT] Leyendo archivo atómico desde: {file_path}")
    
    # Lectura declarando 'null' textual como NaN explicito
    df_raw = pd.read_csv(file_path, na_values=["null", "NULL", "None", "nan", ""])
    
    # Validacion con el nombre real del encabezado
    if "Booking ID" not in df_raw.columns:
        raise KeyError("[ERROR ETL - EXTRACT] El dataset no contiene la columna 'Booking ID'.")
        
    print(f"[EXTRACT] Carga inicial exitosa: {len(df_raw):,} registros leídos.")
    return df_raw