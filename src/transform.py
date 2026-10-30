import pandas as pd
import numpy as np

def transform_data(df_raw: pd.DataFrame):
    print("[TRANSFORM] Iniciando depuración, validación de rangos y modelado dimensional...")
    
    # 1. Copia de trabajo y deduplicación por Booking ID
    df_clean = df_raw.copy()
    df_clean = df_clean.drop_duplicates(subset=["Booking ID"]).reset_index(drop=True)
    
    # Limpieza de comillas y espacios en IDs
    for col in ["Booking ID", "Customer ID"]:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.replace('"', '').str.strip()

    # 2. Reemplazo de cadenas "null" a NaN real
    df_clean = df_clean.replace(["null", "Null", "NULL", "nan", "NaN", ""], np.nan)

    # 3. Quality Gates (Filtros de rangos)
    outliers_count = 0
    if "Booking Value" in df_clean.columns:
        outliers_bv = df_clean[(df_clean["Booking Value"] < 0) | (df_clean["Booking Value"] > 10000)].shape[0]
        df_clean.loc[(df_clean["Booking Value"] < 0) | (df_clean["Booking Value"] > 10000), "Booking Value"] = np.nan
        outliers_count += outliers_bv

    if "Ride Distance" in df_clean.columns:
        outliers_rd = df_clean[(df_clean["Ride Distance"] < 0.1) | (df_clean["Ride Distance"] > 500)].shape[0]
        df_clean.loc[(df_clean["Ride Distance"] < 0.1) | (df_clean["Ride Distance"] > 500), "Ride Distance"] = np.nan
        outliers_count += outliers_rd

    print(f"[TRANSFORM] Depuración y Quality Gates completados. Outliers detectados: {outliers_count}")

    # 4. Normalización de Cancelaciones
    df_clean["Cancelled_By"] = "N/A - Viaje Completado"
    df_clean["Cancellation_Reason"] = "N/A - Viaje Completado"

    mask_cust = df_clean["Cancelled Rides by Customer"] == 1.0
    df_clean.loc[mask_cust, "Cancelled_By"] = "Cliente"
    df_clean.loc[mask_cust, "Cancellation_Reason"] = df_clean.loc[mask_cust, "Reason for cancelling by Customer"].fillna("Razón no especificada")

    mask_driv = df_clean["Cancelled Rides by Driver"] == 1.0
    df_clean.loc[mask_driv, "Cancelled_By"] = "Conductor"
    df_clean.loc[mask_driv, "Cancellation_Reason"] = df_clean.loc[mask_driv, "Driver Cancellation Reason"].fillna("Razón no especificada")

    mask_inc = df_clean["Incomplete Rides"] == 1.0
    df_clean.loc[mask_inc, "Cancelled_By"] = "Sistema / Operación"
    df_clean.loc[mask_inc, "Cancellation_Reason"] = df_clean.loc[mask_inc, "Incomplete Rides Reason"].fillna("Incompleto por sistema")

    # 5. Creación de Dimensiones Cualitativas
    # Dim_Vehiculo
    dim_vehiculo = df_clean[["Vehicle Type"]].drop_duplicates().dropna().reset_index(drop=True)
    dim_vehiculo["Vehicle_SK"] = dim_vehiculo.index + 1
    def clasificar_linea(vtype):
        if vtype in ["eBike", "Bike", "Go Intercity"]: return "Liviana / Económica"
        elif vtype in ["Auto", "Go Sedan"]: return "Estándar"
        else: return "Premium / Carga"
    dim_vehiculo["Business_Line"] = dim_vehiculo["Vehicle Type"].apply(clasificar_linea)
    dim_vehiculo = dim_vehiculo[["Vehicle_SK", "Vehicle Type", "Business_Line"]]

    # Dim_MetodoPago
    dim_pago = df_clean[["Payment Method"]].drop_duplicates().dropna().reset_index(drop=True)
    dim_pago["Payment_SK"] = dim_pago.index + 1
    dim_pago = dim_pago[["Payment_SK", "Payment Method"]]

    # Dim_Cancelacion
    dim_cancelacion = df_clean[["Cancelled_By", "Cancellation_Reason"]].drop_duplicates().reset_index(drop=True)
    dim_cancelacion["Cancellation_SK"] = dim_cancelacion.index + 1
    dim_cancelacion = dim_cancelacion[["Cancellation_SK", "Cancelled_By", "Cancellation_Reason"]]

    # 6. Creación de Dim_Tiempo
    df_clean["Date_Parsed"] = pd.to_datetime(df_clean["Date"], errors='coerce')
    if "Time" in df_clean.columns:
        df_clean["Hora"] = pd.to_datetime(df_clean["Time"], format='%H:%M:%S', errors='coerce').dt.hour.fillna(0).astype(int)
    else:
        df_clean["Hora"] = 0

    dim_tiempo = df_clean[["Date_Parsed", "Hora"]].drop_duplicates().dropna().reset_index(drop=True)
    dim_tiempo["Time_SK"] = dim_tiempo["Date_Parsed"].dt.strftime('%Y%m%d').astype(int)
    dim_tiempo["Fecha"] = dim_tiempo["Date_Parsed"].dt.strftime('%Y-%m-%d')
    dim_tiempo["Anio"] = dim_tiempo["Date_Parsed"].dt.year
    dim_tiempo["Mes"] = dim_tiempo["Date_Parsed"].dt.month
    dim_tiempo["Nombre_Mes"] = dim_tiempo["Date_Parsed"].dt.strftime('%B')
    dim_tiempo["Dia"] = dim_tiempo["Date_Parsed"].dt.day
    dim_tiempo["Dia_Semana"] = dim_tiempo["Date_Parsed"].dt.strftime('%A')
    dim_tiempo["Es_Fin_Semana"] = dim_tiempo["Date_Parsed"].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)

    def obtener_franja(hora: int) -> str:
        if 0 <= hora < 6: return "Madrugada"
        elif 6 <= hora < 12: return "Mañana (Pico AM)"
        elif 12 <= hora < 18: return "Tarde"
        else: return "Noche (Pico PM)"

    dim_tiempo["Franja_Horaria"] = dim_tiempo["Hora"].apply(obtener_franja)
    dim_tiempo = dim_tiempo[["Time_SK", "Fecha", "Anio", "Mes", "Nombre_Mes", "Dia", "Dia_Semana", "Es_Fin_Semana", "Hora", "Franja_Horaria"]].drop_duplicates(subset=["Time_SK", "Hora"]).reset_index(drop=True)

    # 7. Mapeo de Claves Foráneas (FKs) a Fact_Bookings
    df_clean["Time_SK"] = df_clean["Date_Parsed"].dt.strftime('%Y%m%d').fillna(0).astype(int)
    
    fact = df_clean.merge(dim_vehiculo, on="Vehicle Type", how="left") \
                   .merge(dim_pago, on="Payment Method", how="left") \
                   .merge(dim_cancelacion, on=["Cancelled_By", "Cancellation_Reason"], how="left")

    fact["Vehicle_SK"] = fact["Vehicle_SK"].fillna(0).astype(int)
    fact["Payment_SK"] = fact["Payment_SK"].fillna(0).astype(int)
    fact["Cancellation_SK"] = fact["Cancellation_SK"].fillna(0).astype(int)

    # Selección final de columnas para la Tabla de Hechos (Máximo 3 métricas cuantitativas)
    fact_bookings = fact[[
        "Booking ID", "Time_SK", "Vehicle_SK", "Payment_SK", "Cancellation_SK",
        "Booking Status", "Customer ID", 
        "Booking Value", "Ride Distance", "Avg VTAT"  # <--- Solo las 3 métricas clave
    ]].copy()

    fact_bookings.rename(columns={
        "Booking ID": "Booking_ID",
        "Booking Status": "Booking_Status",
        "Customer ID": "Customer_ID",
        "Booking Value": "Booking_Value",
        "Ride Distance": "Ride_Distance",
        "Avg VTAT": "Avg_VTAT"
    }, inplace=True)

    metrics = {
        "raw_records": len(df_raw),
        "duplicates_removed": len(df_raw) - len(df_clean),
        "outliers_adjusted": outliers_count,
        "loaded_records": len(fact_bookings),
        "dim_vehiculo_count": len(dim_vehiculo),
        "dim_pago_count": len(dim_pago),
        "dim_cancelacion_count": len(dim_cancelacion),
        "dim_tiempo_count": len(dim_tiempo)
    }

    return fact_bookings, dim_vehiculo, dim_pago, dim_cancelacion, dim_tiempo, metrics