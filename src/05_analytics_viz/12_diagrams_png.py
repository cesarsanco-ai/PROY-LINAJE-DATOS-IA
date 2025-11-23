# antes: 3_visualizador_lineaje.py

# src/05_analytics_viz/12_diagrams_png.py
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
import sys

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
from config_paths import PROCESSED_DIR, IMG_DIR

# Configuración de Archivos
INPUT_CSV = os.path.join(PROCESSED_DIR, "relaciones_finales.csv")
OUTPUT_IMG_DIR = IMG_DIR

# Aseguramos que exista el directorio de salida
os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)

def generar_diagramas():
    print(f"🎨 Cargando grafo desde: {INPUT_CSV}")
    
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Error: No se encuentra el archivo de relaciones.")
        return

    df = pd.read_csv(INPUT_CSV)

    # Crear Grafo Global
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(row['Origen'], row['Destino'], relation=row['Relacion'])

    print(f"✅ Grafo cargado: {G.number_of_nodes()} nodos.")

    # ==========================================
    # FUNCIÓN PARA DIBUJAR UN SP ESPECÍFICO
    # ==========================================
    def dibujar_sp(nombre_sp):
        # 1. Crear subgrafo (Solo el SP y sus vecinos directos)
        if nombre_sp not in G:
            print(f"⚠️ El SP '{nombre_sp}' no se encontró en el grafo.")
            return

        # Vecinos (Tablas que toca)
        vecinos = list(G.neighbors(nombre_sp)) + list(G.predecessors(nombre_sp))
        subgrafo = G.subgraph([nombre_sp] + vecinos)
        
        plt.figure(figsize=(12, 8))
        # Algoritmo de distribución visual
        pos = nx.spring_layout(subgrafo, seed=42, k=2) 
        
        # Colores de las aristas (flechas)
        edge_colors = []
        for u, v in subgrafo.edges():
            rel = G[u][v]['relation']
            if rel == 'ESCRIBE':
                edge_colors.append('red')    # ROJO = Escritura (Peligroso/Destino)
            elif rel == 'LEE':
                edge_colors.append('blue')   # AZUL = Lectura (Origen)
            else:
                edge_colors.append('gray')   # GRIS = Dependencia genérica

        # Dibujar Nodos
        # El SP central en amarillo, el resto en verde claro
        node_colors = ['gold' if node == nombre_sp else 'lightgreen' for node in subgrafo.nodes()]
        
        nx.draw(subgrafo, pos, 
                with_labels=True, 
                node_color=node_colors, 
                edge_color=edge_colors,
                node_size=2000, 
                font_size=8,
                arrowsize=20,
                width=2)
        
        # Leyenda
        plt.title(f"Linaje del Procedimiento: {nombre_sp}", fontsize=14, fontweight='bold')
        # Truco para la leyenda: plotear líneas vacías con los colores
        plt.plot([], [], color='red', label='ESCRIBE (Insert/Update)')
        plt.plot([], [], color='blue', label='LEE (Select)')
        plt.plot([], [], color='gray', label='USA (Dependencia)')
        plt.legend()
        
        # Guardar
        safe_name = nombre_sp[:50].replace('/', '_').replace('\\', '_')
        filename = os.path.join(OUTPUT_IMG_DIR, f"linaje_{safe_name}.png")
        plt.savefig(filename, format="PNG", dpi=300)
        plt.close()
        print(f"   📸 Imagen generada: {filename}")

    # ==========================================
    # LISTA DE SPs A GRAFICAR
    # ==========================================
    print("🖼️ Generando diagramas para SPs clave...")

    # Lista de ejemplo (puedes modificarla o leerla de un config)
    sps_a_graficar = [
        "RTM_OD_MINORISTA_SP_REPORTES_RUTINA_MATINAL_TEMPORALES_CARGAR",
        "RTM_OD_MINORISTA_SP_LIQUIDADO_VENTA_PRODUCTOS_CARGAR_SECUNDARIO",
        "RTM_OD_MINORISTA_SP_REPORTES_AVANCE_MES_COBERTURAS_CLIENTES_CARGAR" 
    ]

    for sp in sps_a_graficar:
        dibujar_sp(sp)

    print(f"\n✅ Proceso visual completado. Revisa: {OUTPUT_IMG_DIR}")

if __name__ == "__main__":
    generar_diagramas()