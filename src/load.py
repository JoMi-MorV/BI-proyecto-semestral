import sqlite3
import shutil
import os
import pandas as pd
from datetime import datetime

def load_data(fact_df: pd.DataFrame, dim_vehiculo: pd.DataFrame, dim_pago: pd.DataFrame, dim_cancelacion: pd.DataFrame, db_path: str) -> None:
    """
    Carga el Esquema en Estrella en la base de datos relacional SQLite (Data Warehouse).
    Crea índices en Claves Foráneas para optimizar el rendimiento del Dashboard.
    """
    print(f"[LOAD] Guardando tablas analíticas en DWH: {db_path}")
    
    # Asegurar que la carpeta data/processed/ exista
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)

    # Insercion relacional
    dim_vehiculo.to_sql("Dim_Vehiculo", conn, if_exists="replace", index=False)
    dim_pago.to_sql("Dim_MetodoPago", conn, if_exists="replace", index=False)
    dim_cancelacion.to_sql("Dim_Cancelacion", conn, if_exists="replace", index=False)
    fact_df.to_sql("Fact_Bookings", conn, if_exists="replace", index=False)

    # Creación de índices para acelerar filtrados en OLAP / Streamlit / Power BI
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fk_vehiculo ON Fact_Bookings(Vehicle_SK);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fk_pago ON Fact_Bookings(Payment_SK);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fk_cancelacion ON Fact_Bookings(Cancellation_SK);")
    conn.commit()

    conn.close()
    print("[LOAD] Carga dimensional e índices creados exitosamente.")

def archive_raw_file(raw_file_path: str, archive_folder: str) -> None:
    """Copia la fuente procesada a la carpeta archive/ con marca de tiempo."""
    if os.path.exists(raw_file_path):
        os.makedirs(archive_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(raw_file_path)
        archived_name = f"{timestamp}_{base_name}"
        dest_path = os.path.join(archive_folder, archived_name)
        
        shutil.copy(raw_file_path, dest_path)
        print(f"[LOAD] Copia de auditoría almacenada en: {dest_path}")