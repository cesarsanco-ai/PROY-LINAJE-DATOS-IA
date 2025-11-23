# src/config_paths.py
import os

# --- BASE DEL PROYECTO ---
# El archivo está en PROYECTO/src/config_paths.py
# Subimos un nivel para llegar a PROYECTO/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- RUTAS DE DATOS (DATA LAYERS) ---
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "01_raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "02_processed")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "03_knowledge")
GOLD_DIR = os.path.join(DATA_DIR, "04_gold")

# --- RUTAS DE REPORTES (OUTPUTS) ---
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
IMG_DIR = os.path.join(REPORTS_DIR, "diagrams")
DOCS_DIR = os.path.join(REPORTS_DIR, "docs")

# Rutas específicas para EDA
EDA_DIR = os.path.join(REPORTS_DIR, "eda")
EDA_SALUD_DIR = os.path.join(EDA_DIR, "01_salud_sistema")
EDA_PROFUNDO_DIR = os.path.join(EDA_DIR, "02_profundo_codigo")

# --- CONFIGURACIÓN ---
CONFIG_DIR = os.path.join(BASE_DIR, "config")
API_KEY_FILE = os.path.join(CONFIG_DIR, "api_key.txt")

# --- FUNCIONES DE UTILIDAD ---
def ensure_directories():
    """Crea las carpetas clave si no existen"""
    rutas_clave = [
        RAW_DIR, PROCESSED_DIR, KNOWLEDGE_DIR, GOLD_DIR, 
        IMG_DIR, DOCS_DIR, EDA_SALUD_DIR, EDA_PROFUNDO_DIR, CONFIG_DIR
    ]
    for d in rutas_clave:
        os.makedirs(d, exist_ok=True)
        
# Ejecutar creación al importar para asegurar que existan
ensure_directories()