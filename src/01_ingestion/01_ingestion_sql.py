#antes: 1_extraccion_sqlserver.py

# src/01_ingestion/01_ingesta_sql.py
import pyodbc
import pandas as pd
import os
import sys
import time
from dotenv import load_dotenv

# ==============================================
# 1. CONFIGURACIÓN DE RUTAS Y ENTORNO
# ==============================================
# Obtenemos la ruta de este script (src/01_ingestion/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para llegar a 'src/'
src_dir = os.path.dirname(current_dir)
# Agregamos 'src' al path para importar config_paths
sys.path.append(src_dir)

# Importamos las rutas maestras
from config_paths import RAW_DIR, CONFIG_DIR

# Definimos la salida
OUTPUT_DIR = RAW_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================================
# 2. CARGA DE CREDENCIALES (SEGURIDAD)
# ==============================================
# Construimos la ruta al archivo .env
env_path = os.path.join(CONFIG_DIR, ".env")

# Cargamos las variables
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"🔐 Configuración cargada desde: {env_path}")
else:
    print(f"⚠️  ADVERTENCIA: No se encontró .env en {env_path}")

# Leemos las variables de entorno (Evitamos hardcode)
SERVER = os.getenv("SQL_SERVER")
DATABASE = os.getenv("SQL_DATABASE")
USERNAME = os.getenv("SQL_USER")
PASSWORD = os.getenv("SQL_PASSWORD")

# Validación de seguridad
if not all([SERVER, DATABASE, USERNAME, PASSWORD]):
    print("❌ ERROR CRÍTICO: Faltan credenciales en el archivo .env")
    print("   Asegúrate de definir: SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD")
    sys.exit(1)

def get_connection():
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(connection_string)

def run_extraction():
    print(f"🔌 Conectando a {SERVER}...")
    
    try:
        conn = get_connection()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        raise

    # ---------------------------------------------------------
    # 1. DICCIONARIO DE DATOS (Estructura de Tablas)
    # ---------------------------------------------------------
    print("📊 1. Extrayendo estructura de tablas (Columnas y Tipos)...")
    query_columns = """
    SELECT 
        t.name AS [Tabla],
        c.name AS [Columna],
        ty.name AS [Tipo_Dato],
        c.max_length AS [Longitud],
        c.is_nullable AS [Es_Nulo]
    FROM sys.tables t
    INNER JOIN sys.columns c ON t.object_id = c.object_id
    INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
    WHERE t.name LIKE 'od_%' OR t.name LIKE 'XTMP_%' -- Filtro de Negocio
    ORDER BY t.name, c.column_id
    """
    df_cols = pd.read_sql(query_columns, conn)
    df_cols.to_csv(os.path.join(OUTPUT_DIR, "metadata_tablas.csv"), index=False)
    print(f"   -> Guardado: metadata_tablas.csv ({len(df_cols)} columnas encontradas)")

    # ---------------------------------------------------------
    # 2. DEPENDENCIAS DEL SISTEMA
    # ---------------------------------------------------------
    print("🔗 2. Extrayendo dependencias oficiales (Relaciones conocidas)...")
    query_deps = """
    SELECT 
        OBJECT_NAME(d.referencing_id) AS [Origen_SP],
        d.referenced_entity_name AS [Destino_Tabla],
        o.type_desc AS [Tipo_Objeto],
        'DEPENDENCY' AS [Accion]
    FROM sys.sql_expression_dependencies d
    INNER JOIN sys.objects o ON d.referencing_id = o.object_id
    WHERE o.type = 'P' -- Solo Stored Procedures
      AND (d.referenced_entity_name LIKE 'od_%' OR d.referenced_entity_name LIKE 'XTMP_%')
    """
    df_deps = pd.read_sql(query_deps, conn)
    df_deps.to_csv(os.path.join(OUTPUT_DIR, "dependencias_sql.csv"), index=False)
    print(f"   -> Guardado: dependencias_sql.csv ({len(df_deps)} relaciones encontradas)")

    # ---------------------------------------------------------
    # 3. CÓDIGO FUENTE (La materia prima para el Parsing/IA)
    # ---------------------------------------------------------
    print("📜 3. Extrayendo CÓDIGO FUENTE de Stored Procedures...")
    query_code = """
    SELECT 
        o.name AS [Nombre_Objeto],
        o.type_desc AS [Tipo],
        m.definition AS [Codigo_SQL]
    FROM sys.sql_modules m
    INNER JOIN sys.objects o ON m.object_id = o.object_id
    WHERE o.type = 'P' -- Stored Procedures
      AND (
          m.definition LIKE '%od_%' 
          OR m.definition LIKE '%XTMP_%'
          OR m.definition LIKE '%INSERT INTO%'
      )
    """
    df_code = pd.read_sql(query_code, conn)
    
    # Limpiamos saltos de línea para no romper el CSV
    if not df_code.empty:
        df_code['Codigo_SQL'] = df_code['Codigo_SQL'].str.replace('\r', ' ').str.replace('\n', ' ')
    
    df_code.to_csv(os.path.join(OUTPUT_DIR, "codigo_fuente.csv"), index=False)
    print(f"   -> Guardado: codigo_fuente.csv ({len(df_code)} scripts extraídos)")

    conn.close()
    print("\n✅ PROCESO FINALIZADO CON ÉXITO.")
    print(f"📂 Tus archivos están en: {OUTPUT_DIR}")

if __name__ == "__main__":
    try:
        run_extraction()
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("Verifica tu VPN y las credenciales en config/.env")