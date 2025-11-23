# antes: eda_profundo/3_eda_cobertura_ia.py

# actual: src/05_analytics_viz/17_eda_cobertura.py
import pandas as pd
import json
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================
# 1. CONFIGURACIÓN DE RUTAS (NUEVO)
# ==============================================
# Obtenemos la ruta de este script (src/05_analytics_viz/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para llegar a 'src/'
src_dir = os.path.dirname(current_dir)
# Agregamos 'src' al path para importar config_paths
sys.path.append(src_dir)

# Importamos las rutas maestras
from config_paths import RAW_DIR, KNOWLEDGE_DIR, PROCESSED_DIR, EDA_PROFUNDO_DIR

# Configuración de Archivos
FILE_SQL_DEPS = os.path.join(RAW_DIR, "dependencias_sql.csv")
FILE_IA_META = os.path.join(KNOWLEDGE_DIR, "banco_metadata_sp.json")
FILE_MAESTRO_TABLAS = os.path.join(PROCESSED_DIR, "maestro_tablas.csv")
OUTPUT_DIR = os.path.join(EDA_PROFUNDO_DIR, "3_cobertura_imgs")

# Crear carpeta de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Estilo
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = (10, 6)

# ==============================================
# 1. CARGA Y NORMALIZACIÓN
# ==============================================
def cargar_datos():
    print("📂 Cargando datasets para comparación...")
    
    # 1. Dependencias SQL (Oficiales)
    try:
        print(f"   > Leyendo: {FILE_SQL_DEPS}")
        df_sql = pd.read_csv(FILE_SQL_DEPS)
        # Filtramos solo lo que sean dependencias a tablas
        df_sql = df_sql.dropna(subset=['Origen_SP', 'Destino_Tabla'])
        print(f"   ✅ SQL Server reporta: {len(df_sql)} dependencias.")
    except Exception as e:
        print(f"   ❌ Error cargando CSV SQL: {e}")
        return None, None, None

    # 2. Metadata IA
    try:
        print(f"   > Leyendo: {FILE_IA_META}")
        with open(FILE_IA_META, 'r', encoding='utf-8') as f:
            json_ia = json.load(f)
        print(f"   ✅ IA analizó: {len(json_ia)} SPs.")
    except Exception as e:
        print(f"   ❌ Error cargando JSON IA: {e}")
        return None, None, None

    # 3. Maestro de Tablas (Para traducir IDs si fuera necesario)
    mapa_ids = {}
    try:
        if os.path.exists(FILE_MAESTRO_TABLAS):
            df_tablas = pd.read_csv(FILE_MAESTRO_TABLAS)
            mapa_ids = dict(zip(df_tablas['id_tabla'], df_tablas['nombre_tabla']))
    except:
        pass # No es crítico si fallamos aquí, asumiremos nombres directos

    return df_sql, json_ia, mapa_ids

def construir_sets_dependencias(df_sql, json_ia, mapa_ids):
    """Convierte ambos orígenes en Sets de tuplas (SP, TABLA, TIPO) para comparar"""
    print("🔄 Normalizando y cruzando datos...")
    
    # --- SET A: SQL SERVER ---
    # Formato: (Nombre_SP, Nombre_Tabla)
    # Normalizamos a minúsculas para evitar falsos negativos
    set_sql = set()
    for _, row in df_sql.iterrows():
        sp = str(row['Origen_SP']).lower().strip()
        tabla = str(row['Destino_Tabla']).lower().strip()
        set_sql.add((sp, tabla))
        
    # --- SET B: INTELIGENCIA ARTIFICIAL ---
    set_ia = set()
    
    for item in json_ia:
        sp = item.get('nombre_sp', '').lower().strip()
        if not sp: continue
        
        # Procesar Inputs
        for inp in item.get('inputs', []):
            nombre_tabla = mapa_ids.get(inp, inp).lower().strip()
            set_ia.add((sp, nombre_tabla))
            
        # Procesar Outputs
        for out in item.get('outputs', []):
            nombre_tabla = mapa_ids.get(out, out).lower().strip()
            set_ia.add((sp, nombre_tabla))
            
    print(f"   📊 Relaciones únicas normalizadas - SQL: {len(set_sql)}")
    print(f"   📊 Relaciones únicas normalizadas - IA:  {len(set_ia)}")
    
    return set_sql, set_ia

# ==============================================
# 2. ANÁLISIS COMPARATIVO
# ==============================================

def graficar_venn(set_sql, set_ia):
    """Dibuja diagrama de Venn (Overlap) - MANEJO SEGURO DE IMPORTACIÓN"""
    try:
        from matplotlib_venn import venn2
        
        plt.figure(figsize=(10, 8))
        # Intersección
        venn2([set_sql, set_ia], ('SQL Server (Nativo)', 'Inteligencia Artificial'))
        plt.title("Cobertura de Linaje: ¿Cuánto descubrió la IA?")
        plt.savefig(os.path.join(OUTPUT_DIR, "01_venn_cobertura.png"))
        plt.close()
        
    except ImportError:
        print("\n⚠️  ADVERTENCIA: Librería 'matplotlib-venn' no instalada.")
        print("   -> Se omitirá el gráfico de Venn, pero el resto del análisis continuará.")
        return
    except Exception as e:
        print(f"⚠️  Error generando Venn: {e}")
        return

def graficar_gap_barras(set_sql, set_ia):
    """Gráfico de barras comparativo"""
    solo_sql = len(set_sql - set_ia)
    solo_ia = len(set_ia - set_sql)
    ambos = len(set_sql.intersection(set_ia))
    
    categorias = ['Solo detectado por SQL', 'Detectado por Ambos', 'Exclusivo de IA (Valor Agregado)']
    valores = [solo_sql, ambos, solo_ia]
    colores = ['gray', 'steelblue', 'limegreen']
    
    plt.figure()
    bars = plt.bar(categorias, valores, color=colores)
    
    plt.title('Comparativa de Detección de Dependencias')
    plt.ylabel('Cantidad de Relaciones')
    
    # Etiquetas
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height}', ha='center', va='bottom', fontweight='bold')
                 
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "02_gap_analysis.png"))
    plt.close()

def identificar_hallazgos_ia(set_sql, set_ia):
    """Analiza qué tipo de cosas encontró la IA que SQL no"""
    diferencia = set_ia - set_sql
    
    # Clasificar hallazgos
    hallazgos = {
        'Tablas Temporales (#)': 0,
        'Tablas Externas/Stage': 0,
        'Otras': 0
    }
    
    ejemplos = []
    
    for sp, tabla in diferencia:
        if len(ejemplos) < 10:
            ejemplos.append(f"{sp} -> {tabla}")
            
        if tabla.startswith('#') or 'tmp' in tabla:
            hallazgos['Tablas Temporales (#)'] += 1
        elif 'stg' in tabla or 'raw' in tabla:
            hallazgos['Tablas Externas/Stage'] += 1
        else:
            hallazgos['Otras'] += 1
            
    # Graficar si hay datos
    if len(diferencia) > 0:
        plt.figure()
        plt.pie(hallazgos.values(), labels=hallazgos.keys(), autopct='%1.1f%%', colors=['gold', 'coral', 'lightgray'])
        plt.title('¿Qué "Secretos" descubrió la IA?')
        plt.savefig(os.path.join(OUTPUT_DIR, "03_tipologia_hallazgos.png"))
        plt.close()
    
    return hallazgos, ejemplos, len(diferencia)

def generar_reporte_gap(set_sql, set_ia, hallazgos_stats, ejemplos_ia):
    """Reporte de texto final"""
    archivo = os.path.join(OUTPUT_DIR, "reporte_valor_ia.txt")
    
    solo_ia = len(set_ia - set_sql)
    total_universo = len(set_sql.union(set_ia))
    incremento = (solo_ia / len(set_sql)) * 100 if len(set_sql) > 0 else 0
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write("="*50 + "\n")
        f.write("AUDITORÍA DE VALOR DE LA IA (ROI)\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"Relaciones reportadas por SQL Server: {len(set_sql)}\n")
        f.write(f"Relaciones reportadas por IA: {len(set_ia)}\n")
        f.write(f"Universo Total de Relaciones: {total_universo}\n\n")
        
        f.write(f"--- 🚀 IMPACTO ---\n")
        f.write(f"Nuevas relaciones descubiertas: {solo_ia}\n")
        if len(set_sql) > 0:
            f.write(f"Incremento de visibilidad: +{incremento:.1f}%\n")
        f.write("Esto representa el 'Punto Ciego' que SQL Server no estaba viendo.\n\n")
        
        f.write(f"--- 🕵️‍♂️ DESGLOSE DE HALLAZGOS ---\n")
        f.write(f"La IA encontró dependencias ocultas principalmente en:\n")
        for k, v in hallazgos_stats.items():
            f.write(f"- {k}: {v}\n")
            
        f.write(f"\n--- EJEMPLOS CONCRETOS (Top 10) ---\n")
        f.write("Relaciones que solo la IA vio:\n")
        for ej in ejemplos_ia:
            f.write(f"- {ej}\n")

    print(f"📝 Reporte ROI guardado en: {archivo}")

# ==============================================
# MAIN
# ==============================================
if __name__ == "__main__":
    print("🚀 INICIANDO ANÁLISIS DE COBERTURA (SQL vs IA)")
    print("-" * 50)
    
    df_sql, json_ia, mapa_ids = cargar_datos()
    
    if df_sql is not None and json_ia is not None:
        # Procesar
        set_sql, set_ia = construir_sets_dependencias(df_sql, json_ia, mapa_ids)
        
        # Graficar
        print("🎨 Generando comparativas...")
        graficar_venn(set_sql, set_ia)
        graficar_gap_barras(set_sql, set_ia)
        hallazgos, ejemplos, total_nuevos = identificar_hallazgos_ia(set_sql, set_ia)
        
        # Reportar
        generar_reporte_gap(set_sql, set_ia, hallazgos, ejemplos)
        
        print("-" * 50)
        print("✅ ANÁLISIS FINALIZADO.")
        print(f"📂 Revisa la evidencia en: {OUTPUT_DIR}")