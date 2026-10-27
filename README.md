# Estructura de archivos
BI-proyecto-semestral/
│
├── data/                  # Directorio para almacenar los archivos
│   ├── raw/               # Archivos CSV/Excel originales (sin modificar)
│   ├── processed/         # Archivos limpios listos para las herramientas de BI (no subir contenido al git, solo carpeta)
│   └── archive/           # Histórico de archivos ya procesados (opcional/ver funcion, no subir contenido al git, solo carpeta)
│
├── src/                   # Código fuente del proyecto
│   ├── __init__.py        # Convierte la carpeta en un módulo de Python
│   ├── extract.py         # Lectura y validación inicial de los CSVs
│   ├── transform.py       # Limpieza, normalización y reglas de negocio
│   └── load.py            # Exportación a la carpeta processed o base de datos
│
├── notebooks/             # Espacio para análisis exploratorio (EDA) / Ver si mantener o usar otra herramienta de visualización
│   └── exploracion.ipynb
│
├── main.py                # Archivo principal que orquesta todo el flujo
├── requirements.txt       # Dependencias del proyecto (pandas, openpyxl, etc.)
└── .gitignore             # Excluir la carpeta data/ y archivos temporales
