import time
from src.extract import extract_data
from src.transform import transform_data
from src.load import load_data

def run_pipeline():
    start_time = time.time()
    
    # 1. Extracción
    df_raw = extract_data("data/raw/uber_india_2024.csv")
    
    # 2. Transformación
    fact_bookings, dim_vehiculo, dim_pago, dim_cancelacion, dim_tiempo, metrics = transform_data(df_raw)
    
    # 3. Carga
    load_data(fact_bookings, dim_vehiculo, dim_pago, dim_cancelacion, dim_tiempo, db_path="data/processed/uber_dwh.db")
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*50)
    print("      MÉTRICAS OFICIALES DEL PROCESAMIENTO ETL     ")
    print("="*50)
    print(f"- Registros Extraídos (Raw):          {metrics['raw_records']:,}")
    print(f"- Duplicados Eliminados:              {metrics['duplicates_removed']:,}")
    print(f"- Outliers / Anomalías Ajustadas:    {metrics['outliers_adjusted']:,}")
    print(f"- Registros Cargados (Fact_Bookings): {metrics['loaded_records']:,}")
    print(f"- Dimensión Vehículo (Dim_Vehiculo):   {metrics['dim_vehiculo_count']} filas")
    print(f"- Dimensión Pago (Dim_MetodoPago):     {metrics['dim_pago_count']} filas")
    print(f"- Dimensión Cancelación (Dim_Cancel):  {metrics['dim_cancelacion_count']} filas")
    print(f"- Dimensión Tiempo (Dim_Tiempo):       {metrics['dim_tiempo_count']} filas")
    print(f"- Tiempo de Procesamiento ETL:        {elapsed_time:.3f} segundos")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_pipeline()