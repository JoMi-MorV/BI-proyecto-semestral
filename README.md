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


# Ejecución con entrono virtual
1.Crear el entorno virtual:Nombre estandarizado: .venv.Crea la carpeta oculta .venv para aislar las librerías del proyecto de tu sistema operativo:
python3 -m venv .venv

2.Activar el entorno virtual:Linux / Bash / Zsh.Carga las variables de entorno para que Python use los paquetes del entorno aislado:
source venv/bin/activate

3.Instalar las dependencias del proyecto:Pandas y OpenPyXL.
Actualiza el gestor de paquetes pip e instala las librerías declaradas en requirements.txt:
pip install -r requirements.txt

4.Ejecutar el Pipeline ETL:Generación del DWH SQLite.Ejecuta el script orquestador principal:
python main.py

