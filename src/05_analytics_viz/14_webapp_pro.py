#antes: 4_5_app_streamlit.py

# actual:  src/05_analytics_viz/14_webapp_pro.py
import streamlit as st
import pandas as pd
import networkx as nx
import os
import sys
from collections import deque
from openai import OpenAI

# ==============================================
# 1. CONFIGURACIÓN DE RUTAS (NUEVO PATRÓN)
# ==============================================
# Obtenemos la ruta de este script (src/05_analytics_viz/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para llegar a 'src/'
src_dir = os.path.dirname(current_dir)
# Agregamos 'src' al path para importar config_paths
sys.path.append(src_dir)

# Importamos las rutas maestras
from config_paths import PROCESSED_DIR, RAW_DIR, API_KEY_FILE

# ==============================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================
st.set_page_config(page_title="Gloria RTM - Linaje IA (PRO)", layout="wide")

# ==============================================
# FUNCIONES BACKEND
# ==============================================

@st.cache_data
def cargar_datos():
    """Carga Grafo y Diccionario de Código Fuente"""
    
    # 1. Cargar Relaciones (Grafo) desde PROCESSED
    ruta_rel = os.path.join(PROCESSED_DIR, "relaciones_finales.csv")
    if not os.path.exists(ruta_rel):
        return None, None, None

    df_rel = pd.read_csv(ruta_rel)
    G = nx.DiGraph()
    for _, row in df_rel.iterrows():
        G.add_edge(row['Origen'], row['Destino'], tipo=row['Relacion'])
    
    # 2. Cargar Código Fuente (Diccionario para búsqueda rápida) desde RAW
    ruta_code = os.path.join(RAW_DIR, "codigo_fuente.csv")
    diccionario_codigo = {}
    
    if os.path.exists(ruta_code):
        df_code = pd.read_csv(ruta_code)
        # Creamos un mapa: Nombre_Objeto -> Codigo_SQL
        # Normalizamos nombres a mayúsculas por si acaso
        # Manejo seguro de nulos
        df_code = df_code.dropna(subset=['Nombre_Objeto', 'Codigo_SQL'])
        diccionario_codigo = pd.Series(df_code.Codigo_SQL.values, index=df_code.Nombre_Objeto).to_dict()
    
    return G, df_rel, diccionario_codigo

def cargar_api_key():
    try:
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def consultar_openai_rag(cliente, mensaje_usuario, contexto_sql, prompt_sistema=None):
    """
    RAG MEJORADO: Soporta múltiples objetos y contextos
    """
    if not prompt_sistema:
        prompt_sistema = """
        Eres un Arquitecto de Datos experto en T-SQL. 
        Tu trabajo es explicar el linaje y la lógica de negocio basándote EXCLUSIVAMENTE en el código SQL proporcionado.
        Sé técnico, breve y directo. Si la respuesta no está en el código, dilo.
        """
    
    # Recorte de seguridad para no exceder tokens
    contexto_safe = contexto_sql[:15000] if contexto_sql else "-- No hay código disponible"
    
    prompt_usuario_final = f"""
    CONTEXTO SQL (Código Fuente de los objetos relacionados):
    ```sql
    {contexto_safe}
    ```

    PREGUNTA DEL USUARIO:
    {mensaje_usuario}

    INSTRUCCIÓN: Si analizas una TABLA, explica CÓMO se alimenta basándote en los SPs proporcionados.
    """

    try:
        response = cliente.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario_final}
            ],
            max_tokens=600, 
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error API: {str(e)}"

# --- FUNCIONES AUXILIARES DE GRAFOS (RESTITUIDAS) ---

def encontrar_linaje_mas_profundo(G, tabla_destino):
    """
    Encuentra la ruta más profunda en el linaje usando BFS en el grafo
    """
    # Buscar la ruta más larga desde cualquier origen hasta la tabla destino
    rutas_completas = []
    
    def bfs_desde_origen(nodo_origen):
        queue = deque([(nodo_origen, [nodo_origen])])
        rutas_locales = []
        
        while queue:
            nodo_actual, ruta_actual = queue.popleft()
            
            # Si llegamos a la tabla destino, guardamos la ruta
            if nodo_actual == tabla_destino:
                rutas_locales.append(ruta_actual)
                continue
            
            # Explorar padres (orígenes)
            # Nota: Aquí recorremos hacia adelante (successors) si el origen es la fuente
            # Ojo con la dirección del grafo. Asumimos Origen -> Destino.
            for hijo in G.successors(nodo_actual):
                if hijo not in ruta_actual:  # Evitar ciclos
                    queue.append((hijo, ruta_actual + [hijo]))
        return rutas_locales
    
    # Encontrar todos los nodos raíz (sin predecesores)
    nodos_raiz = [n for n in G.nodes() if G.in_degree(n) == 0]
    
    for raiz in nodos_raiz:
        if nx.has_path(G, raiz, tabla_destino):
            # Usamos shortest_path para validar, pero queremos all_simple_paths para profundidad
            # Para optimizar, usamos un path simple de networkx
            rutas = list(nx.all_simple_paths(G, source=raiz, target=tabla_destino))
            rutas_completas.extend(rutas)
    
    # Encontrar la ruta más larga
    if rutas_completas:
        ruta_mas_larga = max(rutas_completas, key=len)
        return ruta_mas_larga
    else:
        return [tabla_destino]

def visualizar_linaje_ascii(ruta):
    """
    Convierte la ruta en formato ASCII claro
    """
    if len(ruta) == 1:
        return f"🚫 {ruta[0]} no tiene dependencias identificadas hacia atrás."
    
    resultado = "🕸️ **LINAJE IDENTIFICADO (Ruta más larga)**\n\n"
    
    for i, nodo in enumerate(ruta):
        indentacion = "  " * i
        
        if i == 0:
            icono = "🟢"  # Origen
            tipo = "ORIGEN"
        elif i == len(ruta) - 1:
            icono = "🎯"  # Destino
            tipo = "OBJETO ACTUAL"
        elif "SP_" in nodo or "_SP" in nodo:
            icono = "⚙️ "  # Stored Procedure
            tipo = "PROCESO"
        else:
            icono = "📊"  # Tabla
            tipo = "TABLA"
        
        resultado += f"{indentacion}{icono} **{nodo}**\n"
        
        if i < len(ruta) - 1:
            resultado += f"{indentacion}  ⬇️\n"
    
    return resultado

# ==============================================
# INICIALIZACIÓN
# ==============================================
G, df_rel, dic_codigo = cargar_datos()

if G is None:
    st.error(f"⚠️ Faltan archivos de datos en {PROCESSED_DIR} o {RAW_DIR}. Ejecuta la ingesta primero.")
    st.stop()

api_key = cargar_api_key()
client = None
if api_key:
    client = OpenAI(api_key=api_key)

# ==============================================
# INTERFAZ
# ==============================================
st.title("🕵️‍♂️ Auditoría de Linaje de Datos (RTM) - PRO")

# Selección de Objeto
opciones = sorted(list(G.nodes()))
seleccion = st.selectbox("🔍 Selecciona Tabla o SP para analizar:", opciones)

# Recuperamos el código fuente del objeto seleccionado (si existe)
codigo_objeto_actual = dic_codigo.get(seleccion, " -- No se encontró código fuente para este objeto (puede ser una tabla externa).")

# Buscamos vecinos para enriquecer el contexto
padres = list(G.predecessors(seleccion))
hijos = list(G.successors(seleccion))

col1, col2 = st.columns([1.5, 1])

# --- PANEL IZQUIERDO: ESTRUCTURA ---
with col1:
    st.markdown(f"### 🕸️ Estructura: `{seleccion}`")
    
    st.info(f"**Se alimenta de ({len(padres)}):**")
    if padres:
        for p in padres:
            st.write(f"⬅️ {p}")
    else:
        st.write("*(Es origen de datos)*")
        
    st.success(f"**Alimenta a ({len(hijos)}):**")
    if hijos:
        for h in hijos:
            st.write(f"➡️ {h}")
    else:
        st.write("*(Es destino final)*")

    with st.expander("📜 Ver Código SQL Crudo"):
        st.code(codigo_objeto_actual, language="sql")

# --- PANEL DERECHO: INTELIGENCIA ARTIFICIAL ---
with col2:
    st.markdown("### 🤖 Consultar IA (Contextual)")
    
    # Determinar contexto para la IA
    contexto_para_ia = ""
    objetos_analizados = [seleccion]
    
    # SI ES UNA TABLA: Traer código de los SPs que la escriben
    es_tabla = "tb_" in seleccion.lower() or "xtmp_" in seleccion.lower() or "od_" in seleccion.lower()
    
    if es_tabla:
        st.caption(f"🔍 La IA analizará los SPs que escriben en: {seleccion}")
        
        # Buscar SPs que ESCRIBEN en esta tabla (Predecesores en el grafo)
        # En nuestro grafo: Origen -> Destino. Si SP escribe en Tabla: SP -> Tabla.
        # Por tanto, buscamos Predecesores.
        sps_que_escriben = [p for p in padres if any(keyword in p.upper() for keyword in ['SP_', '_SP', 'RTM_'])]
        
        if sps_que_escriben:
            st.success(f"✅ Encontrados {len(sps_que_escriben)} SPs padres")
            
            # Concatenar código de TODOS los SPs padres
            codigos_encontrados = 0
            for sp in sps_que_escriben[:5]:  # Límite a 5 SPs para no reventar tokens
                codigo_sp = dic_codigo.get(sp, "")
                if codigo_sp and len(codigo_sp) > 50:
                    contexto_para_ia += f"\n\n-- CÓDIGO PADRE: {sp} --\n{codigo_sp}"
                    objetos_analizados.append(sp)
                    codigos_encontrados += 1
            
            if codigos_encontrados > 0:
                st.info(f"📝 Contexto cargado: {codigos_encontrados} SPs")
            else:
                contexto_para_ia = " -- Sin código disponible de los padres"
                
        else:
            contexto_para_ia = " -- No se encontraron SPs directos que alimenten esta tabla"
            
    else:
        st.caption(f"La IA analizará el código de: {seleccion}")
        contexto_para_ia = codigo_objeto_actual

    # OPCIONES ESPECÍFICAS PARA TRAZABILIDAD
    tipo_consulta = st.radio("Tipo de análisis:", 
             ["🔍 Trazabilidad completa (linaje)", 
              "📊 Explicar lógica de negocio",
              "⚙️  Análisis técnico detallado",
              "❓ Pregunta libre..."])
    
    user_input = ""
    prompt_especifico = None

    if tipo_consulta == "❓ Pregunta libre...":
        user_input = st.text_area("Escribe tu pregunta específica:")
    else:
        # Asignar preguntas específicas para cada tipo
        if tipo_consulta == "🔍 Trazabilidad completa (linaje)":
            user_input = "Identifica la SECUENCIA COMPLETA de linaje. Muestra la cadena de dependencias en formato ASCII."
            prompt_especifico = """
            TRAZABILIDAD DE LINAJE:
            Genera un árbol de texto simple mostrando de dónde vienen los datos y hacia dónde van.
            Usa formato:
            Nivel 0: [Tabla Objetivo]
              ↳ Nivel 1: [Proceso Padre]
                 ↳ Nivel 2: [Tabla Origen]
            """
        elif tipo_consulta == "📊 Explicar lógica de negocio":
            user_input = "Explica brevemente la lógica de negocio principal en lenguaje natural."
        elif tipo_consulta == "⚙️ Análisis técnico detallado":
            user_input = "Analiza transformaciones técnicas: filtros WHERE, JOINs críticos y GROUP BY."
        
        st.info(f"🔍 Análisis seleccionado: {tipo_consulta}")

    if st.button("✨ Ejecutar Análisis"):
        if not client:
            st.error("Falta API Key")
        elif len(contexto_para_ia) < 50:
            st.warning("No hay suficiente código fuente para análisis profundo.")
        else:
            with st.spinner("Analizando trazabilidad..."):
                
                # Llamada a la IA
                respuesta = consultar_openai_rag(client, user_input, contexto_para_ia, prompt_especifico)
                
                # Mostrar respuesta
                st.markdown("### 🕸️ Resultado Trazabilidad")
                
                if tipo_consulta == "🔍 Trazabilidad completa (linaje)":
                    st.markdown("**Interpretación de IA:**")
                    st.markdown(respuesta)
                    
                    # Visualización Algorítmica (Backup)
                    # st.markdown("---")
                    # st.markdown("**Cálculo de Grafo (Python puro):**")
                    # ruta_profunda = encontrar_linaje_mas_profundo(G, seleccion)
                    # st.code(visualizar_linaje_ascii(ruta_profunda))
                else:
                    st.markdown(respuesta)

# ==============================================
# TABLA INFERIOR
# ==============================================
st.divider()
st.write("### 📊 Relaciones Crudas")
df_filtrado = pd.concat([df_rel[df_rel['Origen'] == seleccion], df_rel[df_rel['Destino'] == seleccion]])
st.dataframe(df_filtrado, use_container_width=True)