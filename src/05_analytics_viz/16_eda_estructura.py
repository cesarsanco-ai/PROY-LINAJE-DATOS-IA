# antes: eda_profundo/2_eda_estructura_tablas.py

# actual: src/05_analytics_viz/16_eda_estructura.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import numpy as np

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
from config_paths import RAW_DIR, EDA_PROFUNDO_DIR

# Configuración de Archivos
INPUT_FILE = os.path.join(RAW_DIR, "metadata_tablas.csv")
OUTPUT_DIR = os.path.join(EDA_PROFUNDO_DIR, "2_estructura_imgs")

# Crear carpeta de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Estilo de gráficos
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']

# ==============================================
# FUNCIONES DE CARGA Y PROCESAMIENTO
# ==============================================

def cargar_metadata():
    """Carga el diccionario de datos (tablas y columnas)"""
    print(f"📂 Cargando archivo desde: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print("❌ Error: No se encuentra metadata_tablas.csv")
        return None
    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"✅ Cargadas {len(df)} definiciones de columnas.")
        return df
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return None

def calcular_metricas_tabla(df_cols):
    """Agrupa las columnas para obtener métricas por tabla"""
    print("🧮 Calculando perfil estructural por tabla...")
    
    # Agrupamos por tabla para sacar estadísticas
    perfil_tabla = df_cols.groupby('Tabla').agg(
        n_columnas=('Columna', 'count'),
        n_nulos=('Es_Nulo', 'sum'),
        tipos_distintos=('Tipo_Dato', 'nunique')
    ).reset_index()
    
    # Calcular % de nulidad (Factor de Incertidumbre)
    perfil_tabla['pct_nulos'] = (perfil_tabla['n_nulos'] / perfil_tabla['n_columnas']) * 100
    
    # Clasificar tipo de tabla por prefijo (Heurística)
    def clasificar_tipo(nombre):
        nombre = nombre.lower()
        if 'xtmp' in nombre or '#' in nombre: return 'Temporal (XTMP)'
        if 'od_' in nombre: return 'Operacional (OD)'
        if 'dim' in nombre: return 'Dimensión'
        if 'fact' in nombre: return 'Hechos'
        return 'Otro'
        
    perfil_tabla['categoria'] = perfil_tabla['Tabla'].apply(clasificar_tipo)
    
    return perfil_tabla

def analizar_tipos_dato(df_cols):
    """Analiza la distribución global de tipos de datos"""
    return df_cols['Tipo_Dato'].value_counts()

# ==============================================
# FUNCIONES DE VISUALIZACIÓN
# ==============================================

def graficar_ancho_tablas(perfil_tabla):
    """Histograma: ¿Cuántas columnas tienen mis tablas?"""
    plt.figure()
    sns.histplot(data=perfil_tabla, x='n_columnas', hue='categoria', multiple='stack', bins=30, palette='viridis')
    plt.title('Distribución de "Anchura" de Tablas (Número de Columnas)')
    plt.xlabel('Cantidad de Columnas')
    plt.ylabel('Cantidad de Tablas')
    plt.axvline(perfil_tabla['n_columnas'].mean(), color='red', linestyle='--', label='Promedio')
    plt.legend(title='Categoría')
    plt.savefig(os.path.join(OUTPUT_DIR, "01_anchura_tablas.png"))
    plt.close()

def graficar_top_sabanas(perfil_tabla):
    """Ranking de las tablas más anchas (posibles sábanas desnormalizadas)"""
    top_20 = perfil_tabla.nlargest(20, 'n_columnas').sort_values('n_columnas', ascending=True)
    
    plt.figure(figsize=(12, 10))
    # Color por % de nulos (Más oscuro = Más huecos/nulos)
    bars = plt.barh(top_20['Tabla'], top_20['n_columnas'], color='teal', alpha=0.7)
    
    plt.title('Top 20 Tablas "Sábana" (Mayor cantidad de columnas)')
    plt.xlabel('Número de Columnas')
    
    # Etiquetar valores
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 1, bar.get_y() + bar.get_height()/2, 
                 f'{int(width)} cols', va='center')
                 
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "02_top_tablas_sabana.png"))
    plt.close()

def graficar_distribucion_tipos(conteo_tipos):
    """Pastel/Barras de tipos de datos predominantes"""
    top_tipos = conteo_tipos.head(10)
    otros = pd.Series({'Otros': conteo_tipos.iloc[10:].sum()}) if len(conteo_tipos) > 10 else pd.Series()
    data_plot = pd.concat([top_tipos, otros])
    
    plt.figure()
    data_plot.plot(kind='bar', color='coral')
    plt.title('Top 10 Tipos de Datos Utilizados')
    plt.xlabel('Tipo de Dato SQL')
    plt.ylabel('Frecuencia (Columnas)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "03_distribucion_tipos_datos.png"))
    plt.close()

def graficar_nulidad_vs_ancho(perfil_tabla):
    """Scatter: ¿Las tablas anchas tienen más nulos?"""
    plt.figure()
    sns.scatterplot(data=perfil_tabla, x='n_columnas', y='pct_nulos', 
                    hue='categoria', size='n_columnas', sizes=(20, 200), alpha=0.6)
    
    plt.title('Correlación: Anchura de Tabla vs. Factor de Nulidad')
    plt.xlabel('Número de Columnas')
    plt.ylabel('% de Columnas que permiten NULL')
    plt.axhline(50, color='gray', linestyle=':', label='50% Nulidad')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "04_nulidad_vs_ancho.png"))
    plt.close()

def generar_reporte_texto(perfil_tabla, conteo_tipos):
    """Genera insights textuales"""
    archivo_reporte = os.path.join(OUTPUT_DIR, "reporte_insights_estructura.txt")
    
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        f.write("="*50 + "\n")
        f.write("DIAGNÓSTICO DE ESTRUCTURA DE DATOS (V7)\n")
        f.write("="*50 + "\n\n")
        
        # Métricas Generales
        f.write(f"Total Tablas Analizadas: {len(perfil_tabla)}\n")
        f.write(f"Total Columnas Gestionadas: {perfil_tabla['n_columnas'].sum():,}\n")
        f.write(f"Promedio Columnas por Tabla: {perfil_tabla['n_columnas'].mean():.1f}\n")
        f.write(f"Tabla más ancha: {perfil_tabla.loc[perfil_tabla['n_columnas'].idxmax(), 'Tabla']} ")
        f.write(f"({perfil_tabla['n_columnas'].max()} cols)\n\n")
        
        # Análisis de Tipos
        f.write("--- 💾 USO DE TIPOS DE DATOS ---\n")
        total_cols = conteo_tipos.sum()
        pct_varchar = conteo_tipos.filter(like='char').sum() / total_cols * 100
        pct_fechas = conteo_tipos.filter(like='date').sum() / total_cols * 100
        
        f.write(f"Dominio de Texto (Char/Varchar): {pct_varchar:.1f}%\n")
        f.write(f"Uso de Fechas (Date/Time): {pct_fechas:.1f}%\n")
        if pct_varchar > 70:
            f.write("⚠️ ALERTA: Posible abuso de tipos texto (Stringly Typed Database).\n")
        
        # Análisis de Tablas Sábana
        sabanas = perfil_tabla[perfil_tabla['n_columnas'] > 50]
        f.write(f"\n--- 🛌 TABLAS SÁBANA (>50 columnas) ---\n")
        f.write(f"Cantidad: {len(sabanas)}\n")
        f.write("Listado (Top 5):\n")
        for _, row in sabanas.nlargest(5, 'n_columnas').iterrows():
            f.write(f"- {row['Tabla']}: {row['n_columnas']} cols\n")

    print(f"📝 Reporte guardado en: {archivo_reporte}")

# ==============================================
# MAIN
# ==============================================
if __name__ == "__main__":
    print("🚀 INICIANDO EDA PROFUNDO: ESTRUCTURA DE TABLAS")
    print("-" * 50)
    
    # 1. Cargar
    df_cols = cargar_metadata()
    
    if df_cols is not None:
        # 2. Procesar
        perfil_tabla = calcular_metricas_tabla(df_cols)
        conteo_tipos = analizar_tipos_dato(df_cols)
        
        # 3. Graficar
        print("🎨 Generando gráficos...")
        graficar_ancho_tablas(perfil_tabla)
        graficar_top_sabanas(perfil_tabla)
        graficar_distribucion_tipos(conteo_tipos)
        graficar_nulidad_vs_ancho(perfil_tabla)
        
        # 4. Reportar
        generar_reporte_texto(perfil_tabla, conteo_tipos)
        
        print("-" * 50)
        print("✅ ANÁLISIS FINALIZADO.")
        print(f"📂 Revisa los resultados en: {OUTPUT_DIR}")