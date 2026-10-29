import time
from src.extract import extract_data
from src.transform import transform_data
from src.load import load_data

def run_pipeline():
    start_time = time.time()
    
    # 1. Extracción
    df_raw = extract_data("data/raw/uber_india_2024.csv")
    
    # 2. Transformación
    fact_bookings, dim_vehiculo, dim_pago, dim_cancelacion, metrics = transform_data(df_raw)
    
    # 3. Carga
    load_data(fact_bookings, dim_vehiculo, dim_pago, dim_cancelacion, db_path="data/processed/uber_dwh.db")
    
    execution_time = round(time.time() - start_time, 3)
    
    # Resumen oficial en consola
    print("\n==================================================")
    print("      MÉTRICAS OFICIALES DEL PROCESAMIENTO ETL     ")
    print("==================================================")
    print(f"- Registros Extraídos (Raw):          {metrics['registros_extraidos']:,}")
    print(f"- Duplicados Eliminados:              {metrics['duplicados_eliminados']:,}")
    print(f"- Incompletitudes Estándar (Cancel):  {metrics['nulos_imputados_cancelacion']:,}")
    print(f"- Outliers / Anomalías Ajustadas:    {metrics['outliers_detectados']:,}")  # <-- NUEVA LÍNEA
    print(f"- Registros Cargados (Fact_Bookings): {metrics['registros_fact_bookings']:,}")
    print(f"- Dimensión Vehículo (Dim_Vehiculo):   {metrics['total_dim_vehiculo']} filas")
    print(f"- Dimensión Pago (Dim_MetodoPago):     {metrics['total_dim_pago']} filas")
    print(f"- Dimensión Cancelación (Dim_Cancel):  {metrics['total_dim_cancelacion']} filas")
    print(f"- Tiempo de Procesamiento ETL:        {execution_time} segundos")
    print("==================================================\n")

if __name__ == "__main__":
    run_pipeline()