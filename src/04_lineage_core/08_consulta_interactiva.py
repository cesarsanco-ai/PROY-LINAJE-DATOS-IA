#antes: 6_trazabilidad_tablas.py

# actual: src/04_lineage_core/08_consulta_interactiva.py
import pandas as pd
import json
import os
import sys
from collections import defaultdict, deque

# ==============================================
# 1. CONFIGURACIÓN DE RUTAS (NUEVO)
# ==============================================
# Obtenemos la ruta de este script (src/04_lineage_core/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para llegar a 'src/'
src_dir = os.path.dirname(current_dir)
# Agregamos 'src' al path para importar config_paths
sys.path.append(src_dir)

# Importamos las rutas maestras
from config_paths import RAW_DIR, PROCESSED_DIR, KNOWLEDGE_DIR

def cargar_metadata_sp():
    """Carga el banco de metadata de SPs"""
    try:
        archivo_metadata = os.path.join(KNOWLEDGE_DIR, "banco_metadata_sp.json")
        with open(archivo_metadata, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ banco_metadata_sp.json no encontrado en: {KNOWLEDGE_DIR}")
        return None

def cargar_maestros():
    """Carga todos los maestros necesarios"""
    try:
        df_maestro_sp = pd.read_csv(os.path.join(PROCESSED_DIR, "maestro_sp.csv"))
        df_maestro_tablas = pd.read_csv(os.path.join(PROCESSED_DIR, "maestro_tablas.csv"))
        
        mapeo_nombre_a_id_sp = dict(zip(df_maestro_sp['nombre_sp'], df_maestro_sp['id_sp']))
        mapeo_id_a_nombre_tabla = dict(zip(df_maestro_tablas['id_tabla'], df_maestro_tablas['nombre_tabla']))
        mapeo_nombre_a_id_tabla = dict(zip(df_maestro_tablas['nombre_tabla'], df_maestro_tablas['id_tabla']))
        
        return mapeo_nombre_a_id_sp, mapeo_id_a_nombre_tabla, mapeo_nombre_a_id_tabla
        
    except FileNotFoundError as e:
        print(f"❌ Error cargando maestros: {e}")
        return None, None, None

def encontrar_sp_por_id(sp_id, metadata_sp):
    """Busca un SP por ID en la metadata"""
    for sp in metadata_sp:
        if sp['id_sp'].lower() == sp_id.lower():
            return sp
    return None

def encontrar_sp_por_nombre(sp_nombre, metadata_sp, mapeo_nombre_a_id_sp):
    """Busca un SP por nombre en la metadata"""
    sp_id = mapeo_nombre_a_id_sp.get(sp_nombre)
    if sp_id:
        return encontrar_sp_por_id(sp_id, metadata_sp)
    return None

def construir_arbol_trazabilidad(tabla_objetivo, metadata_sp, mapeo_nombre_a_id_sp, mapeo_id_a_nombre_tabla, mapeo_nombre_a_id_tabla, max_profundidad=10):
    """
    Construye un árbol completo de trazabilidad usando BFS
    """
    print(f"🌳 CONSTRUYENDO ÁRBOL DE TRAZABILIDAD PARA: {tabla_objetivo}")
    print("=" * 60)
    
    # Cargar dependencias del CSV (Datos crudos)
    try:
        df_deps = pd.read_csv(os.path.join(RAW_DIR, "dependencias_sql.csv"))
    except FileNotFoundError:
        print(f"❌ No se pudo cargar dependencias_sql.csv desde {RAW_DIR}")
        return None
    
    # Estructura del árbol
    arbol = {
        'tabla_raiz': tabla_objetivo,
        'niveles': {},
        'tablas_origen': set(),
        'sps_involucrados': set(),
        'profundidad_maxima': 0
    }
    
    # Cola para BFS: (tabla, nivel, camino)
    cola = deque()
    cola.append((tabla_objetivo, 0, []))
    visitados = set()
    
    while cola:
        tabla_actual, nivel_actual, camino_actual = cola.popleft()
        
        if nivel_actual > max_profundidad:
            continue
            
        if tabla_actual in visitados:
            continue
            
        visitados.add(tabla_actual)
        arbol['profundidad_maxima'] = max(arbol['profundidad_maxima'], nivel_actual)
        
        # Buscar SPs que forman esta tabla
        sps_formadores = df_deps[df_deps['Destino_Tabla'] == tabla_actual]['Origen_SP'].unique()
        
        if nivel_actual not in arbol['niveles']:
            arbol['niveles'][nivel_actual] = []
        
        if len(sps_formadores) == 0:
            # Esta es una tabla origen (no tiene SPs que la formen)
            arbol['tablas_origen'].add(tabla_actual)
            arbol['niveles'][nivel_actual].append({
                'tipo': 'TABLA_ORIGEN',
                'nombre': tabla_actual,
                'sps_formadores': [],
                'camino': camino_actual.copy()
            })
            continue
        
        # Procesar cada SP formador
        for sp_nombre in sps_formadores:
            sp_meta = encontrar_sp_por_nombre(sp_nombre, metadata_sp, mapeo_nombre_a_id_sp)
            arbol['sps_involucrados'].add(sp_nombre)
            
            if sp_meta:
                # Obtener inputs reales (convertir IDs a nombres)
                inputs_reales = []
                for input_id in sp_meta['inputs']:
                    input_nombre = mapeo_id_a_nombre_tabla.get(input_id, input_id)
                    inputs_reales.append(input_nombre)
                
                nodo_sp = {
                    'tipo': 'SP_FORMADOR',
                    'nombre': sp_nombre,
                    'id_sp': sp_meta['id_sp'],
                    'inputs': inputs_reales,
                    'output': tabla_actual,
                    'external_sources': sp_meta.get('external_sources', False),
                    'creates_tables': sp_meta.get('creates_tables', False),
                    'camino': camino_actual.copy() + [f"SP:{sp_nombre}"]
                }
                
                arbol['niveles'][nivel_actual].append(nodo_sp)
                
                # Agregar inputs a la cola para seguir la trazabilidad
                nuevo_camino = camino_actual.copy() + [f"SP:{sp_nombre}", f"TABLA:{tabla_actual}"]
                for input_tabla in inputs_reales:
                    cola.append((input_tabla, nivel_actual + 1, nuevo_camino))
            else:
                # SP sin metadata
                arbol['niveles'][nivel_actual].append({
                    'tipo': 'SP_SIN_METADATA',
                    'nombre': sp_nombre,
                    'output': tabla_actual,
                    'camino': camino_actual.copy()
                })
    
    return arbol

def mostrar_arbol_trazabilidad(arbol):
    """
    Muestra el árbol de trazabilidad de forma visual
    """
    if not arbol:
        print("❌ No se pudo construir el árbol de trazabilidad")
        return
    
    print(f"\n🎯 RESUMEN DEL ÁRBOL DE TRAZABILIDAD")
    print("=" * 50)
    print(f"📊 Tabla raíz: {arbol['tabla_raiz']}")
    print(f"📈 Profundidad máxima: {arbol['profundidad_maxima']} niveles")
    print(f"🔧 SPs involucrados: {len(arbol['sps_involucrados'])}")
    print(f"📦 Tablas origen: {len(arbol['tablas_origen'])}")
    
    # Mostrar por niveles
    for nivel in sorted(arbol['niveles'].keys()):
        print(f"\n📁 NIVEL {nivel}:")
        print("-" * 40)
        
        for nodo in arbol['niveles'][nivel]:
            if nodo['tipo'] == 'TABLA_ORIGEN':
                print(f"   🏁 TABLA ORIGEN: {nodo['nombre']}")
                if nodo['camino']:
                    print(f"      🛣️  Camino: {' → '.join(nodo['camino'])}")
            
            elif nodo['tipo'] == 'SP_FORMADOR':
                print(f"   🔧 SP: {nodo['nombre']} ({nodo['id_sp']})")
                print(f"      📤 Output: {nodo['output']}")
                print(f"      📥 Inputs ({len(nodo['inputs'])}):")
                for input_tabla in nodo['inputs']:
                    print(f"         └─ {input_tabla}")
                print(f"      🔧 Metadata: External={nodo['external_sources']}, CreatesTables={nodo['creates_tables']}")
                if nodo['camino']:
                    print(f"      🛣️  Camino: {' → '.join(nodo['camino'])}")
            
            elif nodo['tipo'] == 'SP_SIN_METADATA':
                print(f"   ⚠️  SP SIN METADATA: {nodo['nombre']}")
                print(f"      📤 Output: {nodo['output']}")

def analizar_rutas_criticas(arbol):
    """
    Analiza las rutas críticas y dependencias importantes
    """
    if not arbol:
        return
    
    print(f"\n🔍 ANÁLISIS DE RUTAS CRÍTICAS")
    print("=" * 50)
    
    # Encontrar SPs con external sources
    sps_externos = []
    for nivel, nodos in arbol['niveles'].items():
        for nodo in nodos:
            if nodo['tipo'] == 'SP_FORMADOR' and nodo['external_sources']:
                sps_externos.append(nodo)
    
    if sps_externos:
        print("🌐 SPs con FUENTES EXTERNAS (críticos):")
        for sp in sps_externos:
            # Encontrar el nivel correcto
            nivel_sp = None
            for nivel, nodos in arbol['niveles'].items():
                if sp in nodos:
                    nivel_sp = nivel
                    break
            print(f"   └─ {sp['nombre']} (Nivel {nivel_sp})")
            print(f"      🛣️  Camino: {' → '.join(sp['camino'])}")
    
    # Encontrar SPs que crean tablas
    sps_creadores = []
    for nivel, nodos in arbol['niveles'].items():
        for nodo in nodos:
            if nodo['tipo'] == 'SP_FORMADOR' and nodo['creates_tables']:
                sps_creadores.append(nodo)
    
    if sps_creadores:
        print(f"\n🏗️  SPs que CREAN TABLAS:")
        for sp in sps_creadores:
            print(f"   └─ {sp['nombre']}")
    
    # Mostrar tablas origen
    if arbol['tablas_origen']:
        print(f"\n🏁 TABLAS ORIGEN (final de la cadena):")
        for tabla in sorted(arbol['tablas_origen']):
            print(f"   └─ {tabla}")

def generar_reporte_completo(tabla_objetivo):
    """
    Genera un reporte completo de trazabilidad
    """
    # Cargar datos
    metadata_sp = cargar_metadata_sp()
    if not metadata_sp:
        return
    
    mapeo_nombre_a_id_sp, mapeo_id_a_nombre_tabla, mapeo_nombre_a_id_tabla = cargar_maestros()
    if not all([mapeo_nombre_a_id_sp, mapeo_id_a_nombre_tabla, mapeo_nombre_a_id_tabla]):
        return
    
    # Verificar que la tabla existe
    if tabla_objetivo not in mapeo_nombre_a_id_tabla:
        print(f"❌ La tabla '{tabla_objetivo}' no existe en el maestro de tablas")
        return
    
    # Construir árbol de trazabilidad
    arbol = construir_arbol_trazabilidad(
        tabla_objetivo, 
        metadata_sp, 
        mapeo_nombre_a_id_sp, 
        mapeo_id_a_nombre_tabla, 
        mapeo_nombre_a_id_tabla,
        max_profundidad=10
    )
    
    if arbol:
        # Mostrar resultados
        mostrar_arbol_trazabilidad(arbol)
        analizar_rutas_criticas(arbol)
        
        # Estadísticas finales
        print(f"\n📊 ESTADÍSTICAS FINALES")
        print("=" * 30)
        print(f"• Tabla analizada: {arbol['tabla_raiz']}")
        print(f"• Profundidad máxima: {arbol['profundidad_maxima']}")
        print(f"• Total SPs involucrados: {len(arbol['sps_involucrados'])}")
        print(f"• Tablas origen identificadas: {len(arbol['tablas_origen'])}")
        print(f"• Niveles con actividad: {len(arbol['niveles'])}")
        
        # Mostrar algunas tablas origen si las hay
        if arbol['tablas_origen']:
            print(f"\n💎 TABLAS ORIGEN MÁS PROFUNDAS:")
            for tabla in list(arbol['tablas_origen'])[:5]:
                print(f"   └─ {tabla}")
            if len(arbol['tablas_origen']) > 5:
                print(f"   ... y {len(arbol['tablas_origen']) - 5} más")
    else:
        print("❌ No se pudo generar el reporte de trazabilidad")

def main():
    """
    Función principal
    """
    print("🔍 SISTEMA DE TRAZABILIDAD COMPLETA (INTERACTIVO V7)")
    print("=" * 40)
    print("💡 Este sistema analiza TODOS los niveles de dependencia")
    print("   usando el banco completo de metadata con IA\n")
    
    # Solicitar tabla
    tabla = input("📝 Ingresa el nombre de la tabla a analizar: ").strip()
    
    if not tabla:
        print("❌ Debes ingresar un nombre de tabla")
        return
    
    print(f"\n🚀 Iniciando análisis completo de: {tabla}")
    print("⏳ Esto puede tomar varios segundos...\n")
    
    # Generar reporte completo
    generar_reporte_completo(tabla)

if __name__ == "__main__":
    main()