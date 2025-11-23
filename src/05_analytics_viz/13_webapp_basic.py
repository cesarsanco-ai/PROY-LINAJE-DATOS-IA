# antes: 4_app_streamlit.py

# src/05_analytics_viz/13_webapp_basic.py
import streamlit as st
import pandas as pd
import networkx as nx
import os
import sys
from openai import OpenAI

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
from config_paths import PROCESSED_DIR, API_KEY_FILE

# ==============================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================
st.set_page_config(page_title="Gloria RTM - Linaje IA (Básico)", layout="wide")

# ==============================================
# FUNCIONES DE BACKEND (GRAFO Y API)
# ==============================================

@st.cache_data
def cargar_grafo():
    """Carga los datos procesados y crea el grafo en memoria."""
    ruta_csv = os.path.join(PROCESSED_DIR, "relaciones_finales.csv")
    
    if not os.path.exists(ruta_csv):
        return None, None

    df_rel = pd.read_csv(ruta_csv)
    G = nx.DiGraph()
    for _, row in df_rel.iterrows():
        G.add_edge(row['Origen'], row['Destino'], tipo=row['Relacion'])
    
    return G, df_rel

def cargar_api_key():
    """Lee la API Key desde el archivo de configuración."""
    try:
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def consultar_openai_generico(cliente, mensaje_usuario):
    """Conecta con GPT-4o-mini para una charla genérica y corta."""
    try:
        response = cliente.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en SQL y Datos. Responde de forma muy breve, concisa y técnica (máximo 2 párrafos)."},
                {"role": "user", "content": mensaje_usuario}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error al conectar con OpenAI: {str(e)}"

# ==============================================
# INICIALIZACIÓN
# ==============================================

# 1. Cargar Grafo
G, df_rel = cargar_grafo()
if G is None:
    st.error("⚠️ No se encontró 'relaciones_finales.csv'. Ejecuta los scripts de procesamiento primero.")
    st.stop()
else:
    st.sidebar.success(f"✅ Grafo cargado: {len(G.nodes())} Nodos")

# 2. Configurar Cliente OpenAI
api_key = cargar_api_key()
client = None
if api_key:
    client = OpenAI(api_key=api_key)
    st.sidebar.success("🔑 API Key Conectada")
else:
    st.sidebar.error("❌ Falta API Key en config/api_key.txt")

# ==============================================
# INTERFAZ PRINCIPAL
# ==============================================
st.title("🕵️‍♂️ Auditoría de Linaje de Datos (RTM)")
st.markdown("### Sistema de Trazabilidad Forense con Grafos + IA (Versión Básica)")

# Buscador Principal
opciones = sorted(list(G.nodes()))
seleccion = st.selectbox("🔍 Buscar Tabla o Stored Procedure:", opciones)

col1, col2 = st.columns([2, 1])

# --- COLUMNA IZQUIERDA: EL GRAFO (ESTÁTICO) ---
with col1:
    st.subheader(f"Resultados para: `{seleccion}`")
    
    vecinos_entrada = list(G.predecessors(seleccion))
    vecinos_salida = list(G.successors(seleccion))
    
    st.write("#### 1. Impacto Directo (Grafo)")
    
    if vecinos_entrada:
        st.info(f"⬅️ **Se alimenta de ({len(vecinos_entrada)}):**")
        for v in vecinos_entrada:
            rel = G[v][seleccion]['tipo']
            st.write(f"- {v} `[{rel}]`")
    else:
        st.write("🔹 Es un nodo raíz (Origen).")

    if vecinos_salida:
        st.success(f"➡️ **Alimenta a ({len(vecinos_salida)}):**")
        for v in vecinos_salida:
            rel = G[seleccion][v]['tipo']
            st.write(f"- {v} `[{rel}]`")
    else:
        st.write("🔸 Es un nodo hoja (Destino Final).")

# --- COLUMNA DERECHA: EL CHAT (DINÁMICO) ---
with col2:
    st.write("#### 2. Consultar IA (Live)")
    st.caption("Chat activo con GPT-4o-mini. Pregunta lo que quieras.")
    
    # Input del usuario
    pregunta_usuario = st.text_area("Escribe tu pregunta:", height=100, placeholder="Ej: Explícame qué es un Stored Procedure...")
    
    if st.button("Enviar a la IA"):
        if not client:
            st.error("No hay API Key configurada.")
        elif not pregunta_usuario:
            st.warning("Escribe una pregunta primero.")
        else:
            with st.spinner("Pensando..."):
                respuesta_ia = consultar_openai_generico(client, pregunta_usuario)
                st.markdown("### 🤖 Respuesta:")
                st.write(respuesta_ia)

# ==============================================
# VISUALIZACIÓN DE DATOS (Inferior)
# ==============================================
st.divider()
st.write("### 🕸️ Explorador de Datos Crudos")
# Usamos pd.concat para compatibilidad
df_filtrado = pd.concat([
    df_rel[df_rel['Origen'] == seleccion],
    df_rel[df_rel['Destino'] == seleccion]
])
st.dataframe(df_filtrado, use_container_width=True)