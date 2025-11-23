# 7_constructor_maestro_trazabilidad.py

# actual: src/04_lineage_core/07_compilador_master.py
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
from config_paths import KNOWLEDGE_DIR, PROCESSED_DIR, GOLD_DIR

def cargar_datos():
    """Carga todos los datos necesarios desde las capas Processed y Knowledge"""
    print("📂 Cargando insumos...")
    try:
        # 1. Metadata de SPs (Viene de la capa KNOWLEDGE - enriquecida por IA)
        path_metadata = os.path.join(KNOWLEDGE_DIR, "banco_metadata_sp.json")
        with open(path_metadata, 'r', encoding='utf-8') as f:
            metadata_sp = json.load(f)
        print(f"   ✅ Metadata cargada: {path_metadata}")
        
        # 2. Maestros (Viene de la capa PROCESSED - normalizada)
        path_maestro = os.path.join(PROCESSED_DIR, "maestro_tablas.csv")
        df_maestro_tablas = pd.read_csv(path_maestro)
        print(f"   ✅ Maestro tablas cargado: {path_maestro}")

        # Crear diccionarios de mapeo
        mapeo_id_a_nombre_tabla = dict(zip(df_maestro_tablas['id_tabla'], df_maestro_tablas['nombre_tabla']))
        mapeo_nombre_a_id_tabla = dict(zip(df_maestro_tablas['nombre_tabla'], df_maestro_tablas['id_tabla']))
        
        return metadata_sp, mapeo_id_a_nombre_tabla, mapeo_nombre_a_id_tabla
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return None, None, None

def identificar_sps_generadores_reales(metadata_sp, mapeo_id_a_nombre_tabla):
    """
    Identifica qué SPs generan realmente cada tabla
    Retorna: {tabla_nombre: [lista_de_sps_generadores]}
    """
    print("🔍 IDENTIFICANDO SPs GENERADORES REALES...")
    
    sps_por_tabla = defaultdict(list)
    
    for sp in metadata_sp:
        sp_id = sp['id_sp']
        sp_nombre = sp.get('nombre_sp', '')
        
        # Obtener outputs REALES (convertir IDs a nombres)
        outputs_reales = []
        for output_id in sp.get('outputs', []):
            output_nombre = mapeo_id_a_nombre_tabla.get(output_id, output_id)
            outputs_reales.append(output_nombre)
        
        # Registrar este SP como generador de cada tabla output
        for tabla_output in outputs_reales:
            sps_por_tabla[tabla_output].append({
                'sp_id': sp_id,
                'sp_nombre': sp_nombre,
                'inputs': [mapeo_id_a_nombre_tabla.get(inp, inp) for inp in sp.get('inputs', [])],
                'external_sources': sp.get('external_sources', False),
                'creates_tables': sp.get('creates_tables', False)
            })
    
    print(f"✅ SPs generadores identificados para {len(sps_por_tabla)} tablas")
    
    # Estadísticas
    total_sps = sum(len(sps) for sps in sps_por_tabla.values())
    print(f"📊 Total relaciones SP→Tabla: {total_sps}")
    
    return dict(sps_por_tabla)

def construir_maestro_trazabilidad(sps_por_tabla, mapeo_nombre_a_id_tabla):
    """
    Construye el maestro de trazabilidad usando memoización
    """
    print("\n🏗️ CONSTRUYENDO MAESTRO DE TRAZABILIDAD...")
    
    maestro = {}
    cache_trazabilidad = {}  # Memoización: {tabla: trazabilidad}
    
    def obtener_trazabilidad_tabla(tabla, visitadas=None):
        """Función recursiva con memoización"""
        if visitadas is None:
            visitadas = set()
        
        # Si ya está en cache, retornar resultado
        if tabla in cache_trazabilidad:
            return cache_trazabilidad[tabla]
        
        # Evitar ciclos infinitos
        if tabla in visitadas:
            return {'es_origen': True, 'tablas_origen': {tabla}, 'profundidad': 0}
        
        visitadas.add(tabla)
        
        # Obtener SPs que generan esta tabla
        sps_generadores = sps_por_tabla.get(tabla, [])
        
        if not sps_generadores:
            # Esta es una tabla origen
            resultado = {
                'es_origen': True,
                'tablas_origen': {tabla},
                'profundidad': 0,
                'sps_generadores': []
            }
        else:
            # Procesar cada SP generador
            tablas_origen_totales = set()
            profundidad_maxima = 0
            sps_detallados = []
            
            for sp in sps_generadores:
                # Para cada input del SP, obtener su trazabilidad
                inputs_trazabilidad = []
                profundidad_sp = 0
                
                for input_tabla in sp['inputs']:
                    trazabilidad_input = obtener_trazabilidad_tabla(input_tabla, visitadas.copy())
                    inputs_trazabilidad.append({
                        'tabla': input_tabla,
                        'trazabilidad': trazabilidad_input
                    })
                    # Actualizar tablas origen y profundidad
                    tablas_origen_totales.update(trazabilidad_input['tablas_origen'])
                    profundidad_sp = max(profundidad_sp, trazabilidad_input['profundidad'] + 1)
                
                sps_detallados.append({
                    'sp_id': sp['sp_id'],
                    'sp_nombre': sp['sp_nombre'],
                    'inputs': sp['inputs'],
                    'inputs_trazabilidad': inputs_trazabilidad,
                    'external_sources': sp['external_sources'],
                    'creates_tables': sp['creates_tables'],
                    'profundidad_contribucion': profundidad_sp
                })
                
                profundidad_maxima = max(profundidad_maxima, profundidad_sp)
            
            # Convertir sets a listas para JSON serializable
            resultado = {
                'es_origen': False,
                'tablas_origen': list(tablas_origen_totales),
                'profundidad': profundidad_maxima,
                'sps_generadores': sps_detallados,
                'total_sps_generadores': len(sps_generadores)
            }
        
        # Guardar en cache
        cache_trazabilidad[tabla] = resultado
        return resultado
    
    # Procesar todas las tablas que tienen SPs generadores
    tablas_con_sps = list(sps_por_tabla.keys())
    print(f"📋 Procesando {len(tablas_con_sps)} tablas con SPs generadores...")
    
    for i, tabla in enumerate(tablas_con_sps, 1):
        if i % 100 == 0:
            print(f"   Procesadas {i}/{len(tablas_con_sps)} tablas...")
        
        tabla_id = mapeo_nombre_a_id_tabla.get(tabla, f"T_{tabla[:10]}")
        
        # Convertir sets internos a listas antes de guardar en el maestro final
        resultado_traza = obtener_trazabilidad_tabla(tabla)
        if isinstance(resultado_traza.get('tablas_origen'), set):
            resultado_traza['tablas_origen'] = list(resultado_traza['tablas_origen'])

        maestro[tabla] = {
            'tabla_id': tabla_id,
            'trazabilidad': resultado_traza
        }
    
    print(f"✅ Maestro construido con {len(maestro)} tablas")
    return maestro, cache_trazabilidad

def mostrar_estadisticas_maestro(maestro):
    """Muestra estadísticas del maestro de trazabilidad"""
    print("\n📊 ESTADÍSTICAS DEL MAESTRO:")
    print("=" * 40)
    
    total_tablas = len(maestro)
    tablas_origen = 0
    profundidad_maxima = 0
    total_sps = 0
    
    for tabla, info in maestro.items():
        trazabilidad = info['trazabilidad']
        if trazabilidad['es_origen']:
            tablas_origen += 1
        else:
            total_sps += trazabilidad.get('total_sps_generadores', 0)
            profundidad_maxima = max(profundidad_maxima, trazabilidad.get('profundidad', 0))
    
    print(f"• Tablas en el sistema: {total_tablas}")
    print(f"• Tablas origen (sin SPs): {tablas_origen}")
    print(f"• Tablas generadas por SPs: {total_tablas - tablas_origen}")
    print(f"• Total SPs generadores: {total_sps}")
    print(f"• Profundidad máxima: {profundidad_maxima} niveles")
    
    # Top 5 tablas más complejas
    tablas_complejas = []
    for tabla, info in maestro.items():
        if not info['trazabilidad']['es_origen']:
            complejidad = len(info['trazabilidad'].get('tablas_origen', []))
            tablas_complejas.append((tabla, complejidad))
    
    tablas_complejas.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 TOP 5 TABLAS MÁS COMPLEJAS:")
    for tabla, complejidad in tablas_complejas[:5]:
        print(f"   {tabla}: {complejidad} tablas origen")

def consultar_trazabilidad_tabla(maestro, tabla_consulta):
    """Consulta la trazabilidad de una tabla específica"""
    if tabla_consulta not in maestro:
        print(f"❌ La tabla '{tabla_consulta}' no está en el maestro")
        return None
    
    info = maestro[tabla_consulta]
    trazabilidad = info['trazabilidad']
    
    print(f"\n🎯 TRAZABILIDAD DE: {tabla_consulta} ({info['tabla_id']})")
    print("=" * 60)
    
    if trazabilidad['es_origen']:
        print("🏁 ESTA ES UNA TABLA ORIGEN")
        print("   (No es generada por ningún SP)")
    else:
        print(f"📊 GENERADA POR {trazabilidad['total_sps_generadores']} SPs")
        print(f"📈 PROFUNDIDAD: {trazabilidad['profundidad']} niveles")
        print(f"🏁 TABLAS ORIGEN: {len(trazabilidad['tablas_origen'])}")
        
        print(f"\n🔧 SPs GENERADORES:")
        for sp in trazabilidad['sps_generadores']:
            print(f"   • {sp['sp_id']} - {sp['sp_nombre']}")
            print(f"     Inputs: {len(sp['inputs'])} tablas")
            if sp['external_sources']:
                print(f"     🌐 TIENE FUENTES EXTERNAS")
        
        print(f"\n🌳 RAMAS DE TRAZABILIDAD (formato compacto):")
        # Generar representación compacta de las ramas
        ramas = generar_ramas_compactas(trazabilidad)
        for i, rama in enumerate(ramas[:10], 1):  # Mostrar solo 10 ramas
            print(f"   {i:2d}. {rama}")

def generar_ramas_compactas(trazabilidad):
    """Genera representación compacta de las ramas de trazabilidad"""
    if trazabilidad['es_origen']:
        # Convertir a string si es lista
        origen = trazabilidad['tablas_origen']
        if isinstance(origen, list):
            origen = ",".join(origen)
        return [f"T:{origen}"]
    
    ramas = []
    for sp in trazabilidad['sps_generadores']:
        for input_info in sp['inputs_trazabilidad']:
            input_tabla = input_info['tabla']
            sub_ramas = generar_ramas_compactas(input_info['trazabilidad'])
            for sub_rama in sub_ramas:
                ramas.append(f"SP:{sp['sp_id']} → {sub_rama}")
    
    return ramas[:20]  # Limitar a 20 ramas

def guardar_maestro(maestro, nombre_archivo="maestro_trazabilidad_completo.json"):
    """Guarda el maestro en la carpeta GOLD"""
    try:
        ruta_salida = os.path.join(GOLD_DIR, nombre_archivo)
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(maestro, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Maestro guardado exitosamente en:\n   {ruta_salida}")
    except Exception as e:
        print(f"❌ Error guardando maestro: {e}")

def main():
    """Función principal"""
    print("🏗️ CONSTRUCTOR DE MAESTRO DE TRAZABILIDAD (V7)")
    print("=" * 50)
    print("💡 Estrategia: Bottom-up con Memoización\n")
    
    # Cargar datos
    metadata_sp, mapeo_id_a_nombre_tabla, mapeo_nombre_a_id_tabla = cargar_datos()
    if not all([metadata_sp, mapeo_id_a_nombre_tabla, mapeo_nombre_a_id_tabla]):
        return
    
    # Paso 1: Identificar SPs generadores reales
    sps_por_tabla = identificar_sps_generadores_reales(metadata_sp, mapeo_id_a_nombre_tabla)
    
    # Paso 2: Construir maestro con memoización
    maestro, cache = construir_maestro_trazabilidad(sps_por_tabla, mapeo_nombre_a_id_tabla)
    
    # Paso 3: Mostrar estadísticas
    mostrar_estadisticas_maestro(maestro)
    
    # Paso 4: Guardar maestro
    guardar_maestro(maestro)
    
    # Paso 5: Consulta interactiva
    while True:
        print(f"\n🔍 CONSULTA DE TRAZABILIDAD")
        print("-" * 30)
        tabla_consulta = input("Ingresa nombre de tabla (o 'salir' para terminar): ").strip()
        
        if tabla_consulta.lower() == 'salir':
            break
        
        if tabla_consulta:
            consultar_trazabilidad_tabla(maestro, tabla_consulta)

if __name__ == "__main__":
    main()