#antes: 2_construir_grafo.py

# actual: src/01_ingestion/02_grafo_base.py
import pandas as pd
import networkx as nx
import os
import sys
import sqlglot
from sqlglot import exp

# ==============================================
# 1. CONFIGURACIÓN DE RUTAS (NUEVO)
# ==============================================
# Obtenemos la ruta de este script (src/01_ingestion/)
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

# Aseguramos que exista el directorio de salida (aunque config_paths ya lo hace, es buena práctica)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================================
# 2. CARGA DE INSUMOS
# ==============================================
print(f"🧠 Iniciando análisis de lógica SQL...")
print(f"📂 Leyendo datos desde: {INPUT_DIR}")

# Cargamos dependencias y código fuente
try:
    df_deps = pd.read_csv(os.path.join(INPUT_DIR, "dependencias_sql.csv"))
    df_code = pd.read_csv(os.path.join(INPUT_DIR, "codigo_fuente.csv"))
except FileNotFoundError as e:
    print(f"❌ Error crítico: No se encontraron los archivos en {INPUT_DIR}")
    print(f"   Detalle: {e}")
    exit()

# Inicializamos el Grafo Dirigido (DiGraph)
G = nx.DiGraph()

# ==============================================
# PASO 1: CARGAR EL ESQUELETO (Dependencias Oficiales)
# ==============================================
# Como SQL Server no nos dijo si era lectura/escritura, por defecto
# asumiremos una relación genérica "USA" (luego la refinaremos).
for _, row in df_deps.iterrows():
    sp = row['Origen_SP']
    tabla = row['Destino_Tabla']
    # Nodo SP (Proceso)
    G.add_node(sp, tipo="StoredProcedure", color="red")
    # Nodo Tabla (Dato)
    G.add_node(tabla, tipo="Tabla", color="blue")
    # Arista (Relación preliminar)
    G.add_edge(sp, tabla, relacion="USA")

print(f"   ✅ Estructura base cargada: {G.number_of_nodes()} nodos.")

# ==============================================
# PASO 2: PARSING INTELIGENTE (Detectar XTMP y Dirección)
# ==============================================
print("🕵️‍♂️  Analizando código fuente con SQLGlot para detectar flujo...")

def analizar_codigo_sp(nombre_sp, codigo_sql):
    try:
        # Parseamos el SQL (Transact-SQL)
        parsed = sqlglot.parse(codigo_sql, read="tsql")
        
        # Buscamos todas las sentencias dentro del código
        for expression in parsed:
            
            # 2.1 DETECTAR ESCRITURAS (INSERT / UPDATE)
            # Buscamos tablas destino
            for table in expression.find_all(exp.Table):
                nombre_tabla = table.name
                
                # Verificar si esta tabla está en un contexto de escritura
                # (Esto es una simplificación para el MVP, en prod se navega el árbol)
                padre = table.parent
                es_escritura = False
                
                while padre:
                    if isinstance(padre, (exp.Insert, exp.Update, exp.Create)):
                        es_escritura = True
                        break
                    padre = padre.parent
                
                if es_escritura:
                    # FLUJO: SP -> TABLA
                    G.add_edge(nombre_sp, nombre_tabla, relacion="ESCRIBE")
                    if "XTMP" in nombre_tabla:
                        G.add_node(nombre_tabla, tipo="Temporal", color="orange")
                
                else:
                    # FLUJO: TABLA -> SP (Lectura)
                    # Solo si está en un FROM o JOIN
                    padre = table.parent
                    while padre:
                        if isinstance(padre, (exp.Select, exp.Join)):
                            G.add_edge(nombre_tabla, nombre_sp, relacion="LEE")
                            if "XTMP" in nombre_tabla:
                                G.add_node(nombre_tabla, tipo="Temporal", color="orange")
                            break
                        padre = padre.parent

    except Exception as e:
        # Si falla el parser (común en T-SQL complejo), seguimos
        pass

# Iteramos sobre cada SP y leemos su código
count = 0
for _, row in df_code.iterrows():
    sp_name = row['Nombre_Objeto']
    sql_text = row['Codigo_SQL']
    
    if pd.notna(sql_text):
        analizar_codigo_sp(sp_name, sql_text)
        count += 1

print(f"   ✅ Código analizado en {count} procedimientos.")

# ==============================================
# PASO 3: GUARDAR EL "CEREBRO" (GRAFO)
# ==============================================
print(f"💾 Guardando resultados en: {OUTPUT_DIR}")

# Guardamos en formato GEXF (para visualizar en Gephi) y GraphML (para Python)
nx.write_gexf(G, os.path.join(OUTPUT_DIR, "linaje_completo.gexf"))
nx.write_graphml(G, os.path.join(OUTPUT_DIR, "linaje_completo.graphml"))

# También guardamos una lista de aristas (Edges) en CSV para verla fácil
edges = []
for u, v, data in G.edges(data=True):
    edges.append({"Origen": u, "Destino": v, "Relacion": data.get("relacion", "USA")})

pd.DataFrame(edges).to_csv(os.path.join(OUTPUT_DIR, "relaciones_finales.csv"), index=False)

print(f"\n🎉 GRAFO CONSTRUIDO EXITOSAMENTE.")
print(f"   - Nodos: {G.number_of_nodes()}")
print(f"   - Relaciones: {G.number_of_edges()}")