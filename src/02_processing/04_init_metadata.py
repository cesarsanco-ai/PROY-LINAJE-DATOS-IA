# antes: 4_7_generador_metadata_sp.py

# actual: src/02_processing/04_init_metadata.py
import pandas as pd
import json
import os
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
from config_paths import PROCESSED_DIR, KNOWLEDGE_DIR

# Asignamos las rutas importadas
INPUT_DIR = PROCESSED_DIR      # Donde están los maestros (maestro_sp.csv)
OUTPUT_DIR = KNOWLEDGE_DIR     # Donde guardaremos la metadata (banco_metadata.json)

# Aseguramos que exista el directorio de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generar_metadata_simulada():
    """
    Genera un banco de metadata inicial (esqueleto) para todos los SPs
    """
    print("🎭 INICIALIZANDO BANCO DE METADATA (Estructura V7)...")
    print(f"📂 Leyendo maestros de: {INPUT_DIR}")
    print(f"💾 Guardando metadata en: {OUTPUT_DIR}")
    print("=" * 50)
    
    try:
        # Cargar maestro de SPs
        df_maestro_sp = pd.read_csv(os.path.join(INPUT_DIR, "maestro_sp.csv"))
        
        # Cargar maestro de tablas para usar en inputs/outputs simulados
        df_maestro_tablas = pd.read_csv(os.path.join(INPUT_DIR, "maestro_tablas.csv"))
        
        # Obtener lista de IDs de tablas para usar en la simulación
        ids_tablas = df_maestro_tablas['id_tabla'].tolist()
        
        print(f"📊 Procesando {len(df_maestro_sp)} SPs...")
        
        # Generar metadata simulada para cada SP
        banco_metadata = []
        
        for _, sp_row in df_maestro_sp.iterrows():
            id_sp = sp_row['id_sp']
            nombre_sp = sp_row['nombre_sp']
            
            # Simular inputs y outputs basados en el índice del SP
            # (Esto es un placeholder hasta que pase el script de IA)
            sp_index = int(id_sp.split('_')[1])  # Extraer el número del ID
            
            # Simular inputs (1-3 tablas aleatorias)
            num_inputs = (sp_index % 3) + 1  # 1, 2 o 3 inputs
            inputs_simulados = ids_tablas[:num_inputs]  # Primeras tablas como ejemplo
            
            # Simular outputs (1 tabla)
            outputs_simulados = [ids_tablas[(sp_index % len(ids_tablas))]]
            
            # Simular otros flags basados en el nombre del SP
            external_sources = "cargar" in nombre_sp.lower() or "importar" in nombre_sp.lower()
            creates_tables = "crear" in nombre_sp.lower() or "generar" in nombre_sp.lower()
            
            # Crear objeto de metadata
            metadata_sp = {
                "id_sp": id_sp,
                "nombre_sp": nombre_sp,
                "inputs": inputs_simulados,
                "outputs": outputs_simulados,
                "external_sources": external_sources,
                "creates_tables": creates_tables,
                "ai_review": False # IMPORTANTE: Empieza en False
            }
            
            banco_metadata.append(metadata_sp)
        
        # Guardar como JSON
        archivo_json = os.path.join(OUTPUT_DIR, "banco_metadata_sp.json")
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(banco_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Banco de metadata JSON guardado: {archivo_json}")
        print(f"📊 Total SPs inicializados: {len(banco_metadata)}")
        
        # También guardar como CSV para fácil visualización
        archivo_csv = os.path.join(OUTPUT_DIR, "banco_metadata_sp.csv")
        df_metadata = pd.DataFrame(banco_metadata)
        df_metadata.to_csv(archivo_csv, index=False)
        
        print(f"📄 Copia CSV guardada: {archivo_csv}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ ERROR: No se encontró el archivo {e.filename}")
        print(f"💡 Verifica que hayas ejecutado el paso previo (03_norm_maestros.py)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    generar_metadata_simulada()

if __name__ == "__main__":
    main()