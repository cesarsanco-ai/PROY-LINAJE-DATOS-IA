
# eda_profundo/1_eda_codigo_fuente.py

# actual: src/05_analytics_viz/15_eda_codigo.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import numpy as np
from collections import Counter

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

# Intentar importar WordCloud
try:
    from wordcloud import WordCloud, STOPWORDS
    WORDCLOUD_AVAILABLE = True
except ImportError:
    print("⚠️ Librería 'wordcloud' no detectada. El gráfico de nube de palabras se omitirá.")
    print("💡 Instálala con: pip install wordcloud")
    WORDCLOUD_AVAILABLE = False

# Configuración de Archivos
INPUT_FILE = os.path.join(RAW_DIR, "codigo_fuente.csv")
OUTPUT_DIR = os.path.join(EDA_PROFUNDO_DIR, "1_codigo_imgs")

# Crear carpeta de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Estilo de gráficos
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']

# ==============================================
# FUNCIONES DE ANÁLISIS
# ==============================================

def cargar_datos():
    """Carga el CSV de código fuente"""
    print(f"📂 Cargando archivo desde: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print("❌ Error: No se encuentra codigo_fuente.csv")
        return None
    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"✅ Cargados {len(df)} scripts SQL.")
        # Filtrar vacíos
        df = df.dropna(subset=['Codigo_SQL'])
        return df
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return None

def calcular_metricas(df):
    """Calcula métricas de complejidad, longitud y riesgo"""
    print("🧮 Calculando métricas de código...")
    
    # 1. Normalización
    df['sql_lower'] = df['Codigo_SQL'].str.lower()
    
    # 2. Métricas de Volumen (Obesidad)
    df['n_lineas'] = df['Codigo_SQL'].str.count('\n') + 1
    df['n_caracteres'] = df['Codigo_SQL'].str.len()
    
    # 3. Métricas de Complejidad Lógica (Ciclomática Proxy)
    keywords_control = ['if ', 'else', 'case ', 'when ', 'while ', 'cursor ', 'waitfor ']
    df['complejidad_logica'] = 0
    for kw in keywords_control:
        df['complejidad_logica'] += df['sql_lower'].str.count(kw)
    
    # 4. Métricas de Riesgo / Cajas Negras (SQL Dinámico y Destructivo)
    df['sql_dinamico'] = df['sql_lower'].str.contains('exec|sp_executesql|execute ', regex=True).astype(int)
    df['comandos_peligrosos'] = df['sql_lower'].str.count('truncate table|drop table|delete from')
    
    # 5. Volatilidad (Tablas Temporales)
    df['uso_temporales'] = df['sql_lower'].str.count(r'#\w+')
    
    # 6. Perfil CRUD (Booleanos)
    df['tiene_insert'] = df['sql_lower'].str.contains('insert into').astype(int)
    df['tiene_update'] = df['sql_lower'].str.contains('update ').astype(int)
    df['tiene_delete'] = df['sql_lower'].str.contains('delete ').astype(int)
    df['es_lectura_pura'] = ((df['tiene_insert'] == 0) & 
                             (df['tiene_update'] == 0) & 
                             (df['tiene_delete'] == 0)).astype(int)

    return df

# ==============================================
# FUNCIONES DE VISUALIZACIÓN
# ==============================================

def graficar_distribucion_longitud(df):
    """Histograma de líneas de código"""
    plt.figure()
    sns.histplot(df['n_lineas'], bins=50, kde=True, color='steelblue')
    plt.title('Distribución de Longitud de Código (Líneas)')
    plt.xlabel('Número de Líneas')
    plt.ylabel('Frecuencia')
    plt.axvline(df['n_lineas'].mean(), color='red', linestyle='--', label=f'Media: {df["n_lineas"].mean():.0f}')
    plt.legend()
    plt.savefig(os.path.join(OUTPUT_DIR, "01_distribucion_longitud.png"))
    plt.close()

def graficar_god_objects(df):
    """Ranking de SPs más largos"""
    top_20 = df.nlargest(20, 'n_lineas').sort_values('n_lineas', ascending=True)
    
    plt.figure(figsize=(10, 10))
    plt.barh(top_20['Nombre_Objeto'], top_20['n_lineas'], color='firebrick')
    plt.title('Top 20 "God Objects" (SPs más largos)')
    plt.xlabel('Líneas de Código')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "02_top_god_objects.png"))
    plt.close()

def graficar_complejidad_vs_longitud(df):
    """Scatter plot para ver densidad de lógica"""
    plt.figure()
    sns.scatterplot(data=df, x='n_lineas', y='complejidad_logica', 
                    hue='uso_temporales', size='uso_temporales', sizes=(20, 200), alpha=0.6, palette='viridis')
    plt.title('Complejidad Lógica vs. Longitud del Script')
    plt.xlabel('Líneas de Código')
    plt.ylabel('Puntos de Control (IF/WHILE/CASE)')
    plt.legend(title='Uso Tablas Temp', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "03_complejidad_vs_longitud.png"))
    plt.close()

def graficar_riesgos(df):
    """Barras de riesgos detectados"""
    riesgos = {
        'Usan SQL Dinámico (EXEC)': df['sql_dinamico'].sum(),
        'Usan Tablas Temporales (#)': (df['uso_temporales'] > 0).sum(),
        'Usan Comandos Destructivos (DROP/TRUNC)': (df['comandos_peligrosos'] > 0).sum(),
        'Usan Cursores/Bucles': df['sql_lower'].str.contains('cursor |while ').sum()
    }
    
    plt.figure()
    bars = plt.bar(riesgos.keys(), riesgos.values(), color=['orange', 'skyblue', 'red', 'purple'])
    plt.title('Análisis de Riesgos y Patrones')
    plt.ylabel('Cantidad de SPs')
    plt.xticks(rotation=15)
    
    # Etiquetas
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height}', ha='center', va='bottom')
                 
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "04_riesgos_tecnicos.png"))
    plt.close()

def graficar_perfil_crud(df):
    """Heatmap o barras de operaciones"""
    crud_counts = {
        'Solo Lectura': df['es_lectura_pura'].sum(),
        'Escritura (INSERT)': df['tiene_insert'].sum(),
        'Modificación (UPDATE)': df['tiene_update'].sum(),
        'Eliminación (DELETE)': df['tiene_delete'].sum()
    }
    
    plt.figure()
    plt.pie(crud_counts.values(), labels=crud_counts.keys(), autopct='%1.1f%%', startangle=140, 
            colors=['lightgreen', 'gold', 'orange', 'salmon'])
    plt.title('Perfil Operacional de los Procedimientos')
    plt.savefig(os.path.join(OUTPUT_DIR, "06_perfil_operacional_crud.png"))
    plt.close()

def generar_nube_palabras(df):
    """Genera WordCloud semántico"""
    if not WORDCLOUD_AVAILABLE:
        return

    print("☁️ Generando nube de palabras de negocio...")
    texto_completo = " ".join(df['sql_lower'].dropna())
    
    # Stopwords técnicas SQL para limpiar y dejar solo negocio
    stopwords_sql = set(STOPWORDS)
    stopwords_sql.update([
        'select', 'from', 'where', 'insert', 'into', 'update', 'delete', 'table', 
        'values', 'and', 'or', 'not', 'null', 'as', 'inner', 'join', 'left', 'right', 
        'on', 'case', 'when', 'then', 'else', 'end', 'begin', 'proc', 'procedure',
        'create', 'alter', 'drop', 'exec', 'execute', 'declare', 'set', 'varchar',
        'int', 'decimal', 'date', 'datetime', 'bit', 'return', 'go', 'nolock', 'dbo'
    ])
    
    wc = WordCloud(width=1600, height=800, background_color='white', stopwords=stopwords_sql, colormap='Dark2').generate(texto_completo)
    
    plt.figure(figsize=(20, 10))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.title("Nube de Conceptos (Excluyendo palabras reservadas SQL)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "07_nube_conceptos_negocio.png"))
    plt.close()

def generar_reporte_texto(df):
    """Genera un txt con los insights numéricos"""
    archivo_reporte = os.path.join(OUTPUT_DIR, "reporte_insights_codigo.txt")
    
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        f.write("="*50 + "\n")
        f.write("RADIOGRAFÍA DEL CÓDIGO FUENTE SQL (V7)\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"Total Procedimientos Analizados: {len(df)}\n")
        f.write(f"Total Líneas de Código (LOC): {df['n_lineas'].sum():,}\n")
        f.write(f"Promedio LOC por SP: {df['n_lineas'].mean():.1f}\n\n")
        
        f.write("--- 🚩 TOP RIESGOS ---\n")
        f.write(f"SPs con SQL Dinámico (Caja Negra): {df['sql_dinamico'].sum()} ({df['sql_dinamico'].mean()*100:.1f}%)\n")
        f.write(f"SPs con Lógica Destructiva (DROP/TRUNCATE): {(df['comandos_peligrosos'] > 0).sum()}\n")
        f.write(f"SPs que usan Tablas Temporales (#): {(df['uso_temporales'] > 0).sum()}\n\n")
        
        f.write("--- 🐘 OBJETOS GIGANTES (Top 5) ---\n")
        top5 = df.nlargest(5, 'n_lineas')[['Nombre_Objeto', 'n_lineas']]
        for _, row in top5.iterrows():
            f.write(f"- {row['Nombre_Objeto']}: {row['n_lineas']} líneas\n")
            
        f.write("\n--- 🧠 COMPLEJIDAD LÓGICA ---\n")
        f.write(f"Promedio puntos de decisión (IF/CASE) por SP: {df['complejidad_logica'].mean():.1f}\n")
        complejos = df[df['complejidad_logica'] > df['complejidad_logica'].quantile(0.95)]
        f.write(f"SPs de extrema complejidad (> p95): {len(complejos)}\n")

    print(f"📝 Reporte guardado en: {archivo_reporte}")

# ==============================================
# MAIN
# ==============================================
if __name__ == "__main__":
    print("🚀 INICIANDO EDA PROFUNDO: CÓDIGO FUENTE")
    print("-" * 50)
    
    df = cargar_datos()
    
    if df is not None:
        # Calcular
        df_procesado = calcular_metricas(df)
        
        # Graficar
        print("🎨 Generando gráficos...")
        graficar_distribucion_longitud(df_procesado)
        graficar_god_objects(df_procesado)
        graficar_complejidad_vs_longitud(df_procesado)
        graficar_riesgos(df_procesado)
        graficar_perfil_crud(df_procesado)
        generar_nube_palabras(df_procesado)
        
        # Reportar
        generar_reporte_texto(df_procesado)
        
        print("-" * 50)
        print("✅ ANÁLISIS FINALIZADO.")
        print(f"📂 Revisa los resultados en: {OUTPUT_DIR}")