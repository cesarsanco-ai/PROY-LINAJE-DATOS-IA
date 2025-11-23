# antes: 4_6_generador_maestros.py

# actual: src/02_processing/03_norm_maestros.py
import pandas as pd
import os
import json
import sys

# ==============================================
# 1. CONFIGURACIÓN DE RUTAS (NUEVO)
# ==============================================
# Obtenemos la ruta de este script (src/02_processing/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para llegar a 'src/'
src_dir = os.path.dirname(current_dir)
# Agregamos 'src' al path para importar config_paths
sys.path.append(src_dir)

# Importamos las rutas maestras
from config_paths import RAW_DIR, PROCESSED_DIR

# Asignamos las rutas importadas a las variables locales
INPUT_DIR = RAW_DIR
OUTPUT_DIR = PROCESSED_DIR

# Aseguramos que exista el directorio de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generar_maestros():
    """
    Genera archivos maestros para SPs y Tablas con IDs únicos
    """
    print("🏗️  GENERANDO ARCHIVOS MAESTROS (Estructura V7)...")
    print(f"📂 Leyendo desde: {INPUT_DIR}")
    print(f"💾 Guardando en:  {OUTPUT_DIR}")
    print("=" * 50)
    
    try:
        # Cargar archivo de dependencias
        df_deps = pd.read_csv(os.path.join(INPUT_DIR, "dependencias_sql.csv"))
        df_code = pd.read_csv(os.path.join(INPUT_DIR, "codigo_fuente.csv"))
        
        # ==============================================
        # 1. MAESTRO DE STORED PROCEDURES (JSON)
        # ==============================================
        print("\n📋 GENERANDO MAESTRO DE SPs...")
        
        # Obtener SPs únicos de la columna Origen_SP
        sps_unicos = df_deps['Origen_SP'].unique()
        sps_unicos = sorted([sp for sp in sps_unicos if pd.notna(sp)])
        
        # Crear diccionario para búsqueda rápida de código
        codigo_por_sp = {}
        for _, row in df_code.iterrows():
            sp_name = row['Nombre_Objeto']
            codigo_sql = row['Codigo_SQL']
            if pd.notna(sp_name) and pd.notna(codigo_sql):
                codigo_por_sp[sp_name] = codigo_sql
        
        # Crear lista de SPs con metadata completa
        maestro_sp = []
        for i, sp_name in enumerate(sps_unicos, 1):
            sp_id = f"SP_{i:05d}"  # Formato: SP_00001, SP_00002, etc.
            codigo_sql = codigo_por_sp.get(sp_name, "CÓDIGO NO DISPONIBLE")
            
            maestro_sp.append({
                "id_sp": sp_id, 
                "nombre_sp": sp_name,
                "codigo_sql": codigo_sql
            })
        
        # Guardar maestro de SPs como JSON (mejor para código)
        archivo_sp_json = os.path.join(OUTPUT_DIR, "maestro_sp.json")
        with open(archivo_sp_json, 'w', encoding='utf-8') as f:
            json.dump(maestro_sp, f, indent=2, ensure_ascii=False)
        
        # También guardar versión CSV simplificada (sin código)
        maestro_sp_simple = []
        for sp in maestro_sp:
            maestro_sp_simple.append({
                "id_sp": sp["id_sp"],
                "nombre_sp": sp["nombre_sp"],
                "longitud_codigo": len(sp["codigo_sql"])
            })
        
        df_maestro_sp_simple = pd.DataFrame(maestro_sp_simple)
        archivo_sp_csv = os.path.join(OUTPUT_DIR, "maestro_sp.csv")
        df_maestro_sp_simple.to_csv(archivo_sp_csv, index=False)
        
        print(f"   ✅ Maestro SPs (JSON): {archivo_sp_json}")
        print(f"   ✅ Maestro SPs (CSV simplificado): {archivo_sp_csv}")
        print(f"   📊 Total SPs únicos: {len(sps_unicos)}")
        print(f"   💻 SPs con código disponible: {len([sp for sp in maestro_sp if sp['codigo_sql'] != 'CÓDIGO NO DISPONIBLE'])}")
        
        # ==============================================
        # 2. MAESTRO DE TABLAS
        # ==============================================
        print("\n📊 GENERANDO MAESTRO DE TABLAS...")
        
        # Obtener tablas únicas de la columna Destino_Tabla
        tablas_unicas = df_deps['Destino_Tabla'].unique()
        tablas_unicas = sorted([tb for tb in tablas_unicas if pd.notna(tb)])
        
        # Crear DataFrame con IDs únicos
        maestro_tablas = []
        for i, tabla_name in enumerate(tablas_unicas, 1):
            tabla_id = f"tb_{i:05d}"  # Formato: tb_00001, tb_00002, etc.
            maestro_tablas.append({"id_tabla": tabla_id, "nombre_tabla": tabla_name})
        
        df_maestro_tablas = pd.DataFrame(maestro_tablas)
        
        # Guardar maestro de tablas
        archivo_tablas = os.path.join(OUTPUT_DIR, "maestro_tablas.csv")
        df_maestro_tablas.to_csv(archivo_tablas, index=False)
        
        print(f"   ✅ Maestro Tablas guardado: {archivo_tablas}")
        print(f"   📊 Total tablas únicas: {len(tablas_unicas)}")
        
        # ==============================================
        # 3. GENERAR VERSIÓN NORMALIZADA DE DEPENDENCIAS
        # ==============================================
        print("\n🔗 GENERANDO DEPENDENCIAS NORMALIZADAS...")
        
        # Crear mapeos para búsqueda rápida
        mapeo_sp = {sp["nombre_sp"]: sp["id_sp"] for sp in maestro_sp}
        mapeo_tablas = dict(zip(df_maestro_tablas['nombre_tabla'], df_maestro_tablas['id_tabla']))
        
        # Crear DataFrame normalizado
        dependencias_normalizadas = []
        for _, row in df_deps.iterrows():
            sp_nombre = row['Origen_SP']
            tabla_nombre = row['Destino_Tabla']
            
            if pd.notna(sp_nombre) and pd.notna(tabla_nombre):
                sp_id = mapeo_sp.get(sp_nombre)
                tabla_id = mapeo_tablas.get(tabla_nombre)
                
                if sp_id and tabla_id:
                    dependencias_normalizadas.append({
                        'id_sp': sp_id,
                        'nombre_sp': sp_nombre,
                        'id_tabla': tabla_id, 
                        'nombre_tabla': tabla_nombre,
                        'tipo_objeto': row.get('Tipo_Objeto', ''),
                        'accion': row.get('Accion', '')
                    })
        
        df_deps_normalizado = pd.DataFrame(dependencias_normalizadas)
        
        # Guardar dependencias normalizadas
        archivo_deps_norm = os.path.join(OUTPUT_DIR, "dependencias_normalizadas.csv")
        df_deps_normalizado.to_csv(archivo_deps_norm, index=False)
        
        print(f"   ✅ Dependencias normalizadas guardadas: {archivo_deps_norm}")
        print(f"   📊 Total relaciones: {len(dependencias_normalizadas)}")
        
        # ==============================================
        # 4. RESUMEN FINAL
        # ==============================================
        print("\n🎯 RESUMEN FINAL:")
        print(f"   📁 Carpeta de salida: {OUTPUT_DIR}")
        print(f"   📄 Archivos generados correctamente.")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ ERROR: No se encontró el archivo {e.filename}")
        print(f"💡 Verifica que los archivos .csv estén en: {INPUT_DIR}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    generar_maestros()

if __name__ == "__main__":
    main()