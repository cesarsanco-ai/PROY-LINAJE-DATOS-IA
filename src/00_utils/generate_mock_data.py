
import pandas as pd
import os
import sys

# Add src to path to import config_paths
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from config_paths import RAW_DIR, ensure_directories

def generate_mock_data():
    ensure_directories()
    
    print("🚀 Generando datos de prueba (Mock Data)...")

    # 1. metadata_tablas.csv
    data_tablas = {
        "Tabla": ["od_clientes", "od_clientes", "od_clientes", "od_ventas", "od_ventas", "od_ventas", "XTMP_log", "XTMP_log"],
        "Columna": ["cliente_id", "nombre", "email", "venta_id", "cliente_id", "monto", "log_id", "mensaje"],
        "Tipo_Dato": ["int", "varchar", "varchar", "int", "int", "decimal", "int", "varchar"],
        "Longitud": [4, 100, 100, 4, 4, 18, 4, 255],
        "Es_Nulo": [0, 0, 1, 0, 0, 0, 0, 1]
    }
    df_tablas = pd.DataFrame(data_tablas)
    df_tablas.to_csv(os.path.join(RAW_DIR, "metadata_tablas.csv"), index=False)
    print(f"✅ metadata_tablas.csv generado en {RAW_DIR}")

    # 2. dependencias_sql.csv
    data_deps = {
        "Origen_SP": ["sp_cargar_clientes", "sp_cargar_ventas", "sp_cargar_ventas"],
        "Destino_Tabla": ["od_clientes", "od_ventas", "od_clientes"],
        "Tipo_Objeto": ["SQL_STORED_PROCEDURE", "SQL_STORED_PROCEDURE", "SQL_STORED_PROCEDURE"],
        "Accion": ["DEPENDENCY", "DEPENDENCY", "DEPENDENCY"]
    }
    df_deps = pd.DataFrame(data_deps)
    df_deps.to_csv(os.path.join(RAW_DIR, "dependencias_sql.csv"), index=False)
    print(f"✅ dependencias_sql.csv generado en {RAW_DIR}")

    # 3. codigo_fuente.csv
    # NOTA: Incluimos saltos de línea y formateo básico
    data_code = {
        "Nombre_Objeto": ["sp_cargar_clientes", "sp_cargar_ventas"],
        "Tipo": ["SQL_STORED_PROCEDURE", "SQL_STORED_PROCEDURE"],
        "Codigo_SQL": [
            "CREATE PROCEDURE sp_cargar_clientes AS BEGIN INSERT INTO od_clientes (cliente_id, nombre, email) SELECT id, name, email FROM stage_crm_clientes; END",
            "CREATE PROCEDURE sp_cargar_ventas AS BEGIN -- Carga ventas del dia INSERT INTO od_ventas (venta_id, cliente_id, monto) SELECT id, cli_id, amount FROM stage_pos_sales; UPDATE od_clientes SET ult_compra = GETDATE() WHERE cliente_id IN (SELECT cli_id FROM stage_pos_sales); END"
        ]
    }
    df_code = pd.DataFrame(data_code)
    df_code.to_csv(os.path.join(RAW_DIR, "codigo_fuente.csv"), index=False)
    print(f"✅ codigo_fuente.csv generado en {RAW_DIR}")
    
    print("\n🎉 Datos de prueba generados exitosamente. Ahora puedes ejecutar la FASE 2.")

if __name__ == "__main__":
    generate_mock_data()
