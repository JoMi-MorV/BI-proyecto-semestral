import pandas as pd
import numpy as np
from typing import Tuple, Dict

def transform_data(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
    """
    Aplica limpieza, estandarización semántica, Data Quality Gates (Tratamiento de Outliers)
    y estructuración del Modelo Dimensional (Esquema en Estrella).
    """
    print("[TRANSFORM] Iniciando depuración, validación de rangos y modelado dimensional...")
    
    # 1. Normalizar nombres de columnas (limpiar espacios alrededor)
    df_clean = df_raw.copy()
    df_clean.columns = df_clean.columns.str.strip()

    # Limpieza de valores comillados en Booking ID si existieran
    df_clean["Booking ID"] = df_clean["Booking ID"].astype(str).str.replace('"', '').str.strip()

    # 2. Auditoría y Deduplicación por Clave Natural (Booking ID)
    registros_extraidos = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=["Booking ID"]).copy()
    duplicados_eliminados = registros_extraidos - len(df_clean)
    
    # 3. Consolidación de Causales de Cancelación y Atribución de Responsabilidad
    def consolidar_cancelacion(row):
        status = str(row["Booking Status"]).strip() if pd.notna(row["Booking Status"]) else ""
        cust_reason = str(row["Reason for cancelling by Customer"]).strip() if pd.notna(row["Reason for cancelling by Customer"]) else ""
        driver_reason = str(row["Driver Cancellation Reason"]).strip() if pd.notna(row["Driver Cancellation Reason"]) else ""
        inc_reason = str(row["Incomplete Rides Reason"]).strip() if pd.notna(row["Incomplete Rides Reason"]) else ""

        # Limpiar cadenas que sean "null" textual
        if cust_reason.lower() in ["null", "none", "nan"]: cust_reason = ""
        if driver_reason.lower() in ["null", "none", "nan"]: driver_reason = ""
        if inc_reason.lower() in ["null", "none", "nan"]: inc_reason = ""

        if "Canceled by Customer" in status or "Cancelled by Customer" in status:
            reason = cust_reason if cust_reason != "" else "Motivo No Especificado (Cliente)"
            return reason, "Cliente"
        elif "Canceled by Driver" in status or "Cancelled by Driver" in status or status == "No Driver Found":
            reason = driver_reason if driver_reason != "" else ("Sin Conductor Disponible" if status == "No Driver Found" else "Motivo No Especificado (Conductor)")
            return reason, "Conductor"
        elif "Incomplete" in status:
            reason = inc_reason if inc_reason != "" else "Viaje Incompleto"
            return reason, "Sistema / Operación"
        else:
            return "N/A - Viaje Completado", "N/A"

    res = df_clean.apply(consolidar_cancelacion, axis=1)
    df_clean["Cancellation_Reason"] = [r[0] for r in res]
    df_clean["Cancelled_By"] = [r[1] for r in res]

    # Conteo de nulos estandarizados a "N/A - Viaje Completado"
    nulos_imputados_cancelacion = (df_clean["Cancellation_Reason"] == "N/A - Viaje Completado").sum()

    # 4. Reglas de Negocio: Clasificación por Línea de Negocio
    def obtener_linea_negocio(vehiculo: str) -> str:
        vehiculo = str(vehiculo).strip()
        if vehiculo in ["Auto", "eBike", "Bike", "eBike/Bike"]:
            return "Movilidad Liviana y de Bajo Costo"
        elif vehiculo in ["Go Mini", "Go Sedan"]:
            return "Movilidad Urbana Estándar"
        elif vehiculo in ["Premier Sedan", "UberXL"]:
            return "Movilidad Premium y de Gran Capacidad"
        return "Otros"

    df_clean["Business_Line"] = df_clean["Vehicle Type"].apply(obtener_linea_negocio)

    # 5. DATA QUALITY GATES: Conversión y Aplicación de Filtros de Rangos / Outliers
    metric_cols = ["Booking Value", "Ride Distance", "Avg VTAT", "Avg CTAT", "Customer Rating", "Driver Ratings"]
    for col in metric_cols:
        if col in df_clean.columns:
            # Reemplazar 'null' por NaN y convertir a numérico flotante
            df_clean[col] = df_clean[col].astype(str).str.replace('"', '').str.strip()
            df_clean[col] = df_clean[col].replace(['null', 'None', 'nan', ''], np.nan)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    outliers_detectados = 0

    # Gate 1: Booking Value (0 <= Valor <= 10,000 INR)
    cond_bv = (df_clean["Booking Value"] < 0) | (df_clean["Booking Value"] > 10000)
    outliers_detectados += int(cond_bv.sum())
    df_clean.loc[cond_bv, "Booking Value"] = np.nan

    # Gate 2: Ride Distance (0.1 <= Distancia <= 500 km)
    cond_rd = (df_clean["Ride Distance"] < 0.1) | (df_clean["Ride Distance"] > 500)
    outliers_detectados += int(cond_rd.sum())
    df_clean.loc[cond_rd, "Ride Distance"] = np.nan

    # Gate 3: Tiempos Avg VTAT & Avg CTAT (0 <= Tiempo <= 120 min)
    cond_vtat = (df_clean["Avg VTAT"] < 0) | (df_clean["Avg VTAT"] > 120)
    cond_ctat = (df_clean["Avg CTAT"] < 0) | (df_clean["Avg CTAT"] > 120)
    outliers_detectados += int(cond_vtat.sum()) + int(cond_ctat.sum())
    df_clean.loc[cond_vtat, "Avg VTAT"] = np.nan
    df_clean.loc[cond_ctat, "Avg CTAT"] = np.nan

    # Gate 4: Ratings (1.0 <= Rating <= 5.0)
    cond_cr = (df_clean["Customer Rating"] < 1.0) | (df_clean["Customer Rating"] > 5.0)
    cond_dr = (df_clean["Driver Ratings"] < 1.0) | (df_clean["Driver Ratings"] > 5.0)
    outliers_detectados += int(cond_cr.sum()) + int(cond_dr.sum())
    df_clean.loc[cond_cr, "Customer Rating"] = np.nan
    df_clean.loc[cond_dr, "Driver Ratings"] = np.nan

    # Estandarización de nombres de columnas de ratings
    df_clean["Driver_Rating"] = df_clean["Driver Ratings"]
    df_clean["Customer_Rating"] = df_clean["Customer Rating"]

    # 6. Generación de Tablas de Dimensiones y Claves Sustitutas (SK)
    # Dim_Vehiculo
    dim_vehiculo = df_clean[["Vehicle Type", "Business_Line"]].drop_duplicates().reset_index(drop=True)
    dim_vehiculo.rename(columns={"Vehicle Type": "Vehicle_Type"}, inplace=True)
    dim_vehiculo["Vehicle_SK"] = dim_vehiculo.index + 1

    # Dim_MetodoPago
    dim_pago = df_clean[["Payment Method"]].drop_duplicates().reset_index(drop=True)
    dim_pago.rename(columns={"Payment Method": "Payment_Method"}, inplace=True)
    dim_pago["Payment_SK"] = dim_pago.index + 1

    # Dim_Cancelacion
    dim_cancelacion = df_clean[["Cancellation_Reason", "Cancelled_By"]].drop_duplicates().reset_index(drop=True)
    dim_cancelacion["Cancellation_SK"] = dim_cancelacion.index + 1

    # 7. Mapeo de Claves Foráneas (FK) en Tabla de Hechos (Fact_Bookings)
    df_clean_mapped = df_clean.rename(columns={
        "Vehicle Type": "Vehicle_Type",
        "Payment Method": "Payment_Method",
        "Booking ID": "Booking_ID",
        "Booking Status": "Booking_Status",
        "Booking Value": "Booking_Value",
        "Ride Distance": "Ride_Distance",
        "Avg VTAT": "Avg_VTAT",
        "Avg CTAT": "Avg_CTAT"
    })

    fact_bookings = df_clean_mapped.merge(dim_vehiculo, on=["Vehicle_Type", "Business_Line"], how="left") \
                                   .merge(dim_pago, on="Payment_Method", how="left") \
                                   .merge(dim_cancelacion, on=["Cancellation_Reason", "Cancelled_By"], how="left")

    # Selección final de la estructura desnormalizada para Fact_Bookings
    fact_bookings = fact_bookings[[
        "Booking_ID",
        "Vehicle_SK",
        "Payment_SK",
        "Cancellation_SK",
        "Booking_Status",
        "Booking_Value",
        "Ride_Distance",
        "Avg_VTAT",
        "Avg_CTAT",
        "Customer_Rating",
        "Driver_Rating"
    ]]

    metrics = {
        "registros_extraidos": registros_extraidos,
        "duplicados_eliminados": duplicados_eliminados,
        "nulos_imputados_cancelacion": nulos_imputados_cancelacion,
        "outliers_detectados": outliers_detectados,
        "registros_fact_bookings": len(fact_bookings),
        "total_dim_vehiculo": len(dim_vehiculo),
        "total_dim_pago": len(dim_pago),
        "total_dim_cancelacion": len(dim_cancelacion)
    }

    print(f"[TRANSFORM] Depuración y Quality Gates completados. Outliers detectados: {outliers_detectados}")
    return fact_bookings, dim_vehiculo, dim_pago, dim_cancelacion, metrics