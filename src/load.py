import sqlite3
import pandas as pd
import os

def load_data(fact_bookings, dim_vehiculo, dim_pago, dim_cancelacion, dim_tiempo, db_path: str = "data/processed/uber_dwh.db"):
    print(f"[LOAD] Guardando tablas analíticas en DWH: {db_path}")
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    
    # Cargar las 5 entidades en SQLite
    dim_vehiculo.to_sql("Dim_Vehiculo", conn, if_exists="replace", index=False)
    dim_pago.to_sql("Dim_MetodoPago", conn, if_exists="replace", index=False)
    dim_cancelacion.to_sql("Dim_Cancelacion", conn, if_exists="replace", index=False)
    dim_tiempo.to_sql("Dim_Tiempo", conn, if_exists="replace", index=False)
    fact_bookings.to_sql("Fact_Bookings", conn, if_exists="replace", index=False)

    # Crear índices para alta velocidad de consulta
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_time ON Fact_Bookings(Time_SK);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_vehicle ON Fact_Bookings(Vehicle_SK);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_payment ON Fact_Bookings(Payment_SK);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_cancel ON Fact_Bookings(Cancellation_SK);")
    conn.commit()

    conn.close()
    print("[LOAD] Carga dimensional e índices creados exitosamente.")