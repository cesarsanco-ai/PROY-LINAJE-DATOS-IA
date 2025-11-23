#antes: 8_eda_trazabilidad.py

# actual: src/05_analytics_viz/11_eda_salud.py
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import os
import sys
import numpy as np
from collections import Counter, defaultdict

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
from config_paths import GOLD_DIR, EDA_SALUD_DIR

# Configuración para evitar errores de caracteres especiales
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def cargar_datos():
    """Cargar el JSON de trazabilidad desde GOLD_DIR"""
    try:
        path_archivo = os.path.join(GOLD_DIR, 'maestro_trazabilidad_completo.json')
        print(f"📂 Leyendo archivo maestro desde: {path_archivo}")
        with open(path_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encuentra el archivo en {path_archivo}")
        return None

def preparar_carpeta_salida():
    """Asegura que la carpeta de salida EDA exista"""
    os.makedirs(EDA_SALUD_DIR, exist_ok=True)
    return EDA_SALUD_DIR

def analisis_general_sistema(data, output_dir):
    """Análisis general del sistema"""
    print("📊 Realizando análisis general del sistema...")
    
    # Estadísticas básicas
    metadata = data['metadata']
    tablas = data['tablas']
    
    # Preparar datos para gráficos
    tipos_tabla = [tabla['tipo'] for tabla in tablas.values()]
    uso_tablas = [tabla['estadisticas']['total_sps_usuarios'] for tabla in tablas.values()]
    
    # 1. Distribución de tipos de tablas
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('ANALISIS GENERAL DEL SISTEMA', fontsize=16, fontweight='bold')
    
    # Gráfico de tipos de tabla
    tipo_counts = pd.Series(tipos_tabla).value_counts()
    axes[0,0].pie(tipo_counts.values, labels=tipo_counts.index, autopct='%1.1f%%', startangle=90)
    axes[0,0].set_title('Distribucion de Tipos de Tablas')
    
    # 2. Top 10 tablas más utilizadas
    tablas_uso = [(nombre, tabla['estadisticas']['total_sps_usuarios']) 
                  for nombre, tabla in tablas.items()]
    tablas_uso.sort(key=lambda x: x[1], reverse=True)
    top_10_uso = tablas_uso[:10]
    
    nombres = [x[0][:30] + '...' if len(x[0]) > 30 else x[0] for x in top_10_uso]
    usos = [x[1] for x in top_10_uso]
    
    axes[0,1].barh(nombres, usos, color='skyblue')
    axes[0,1].set_title('Top 10 Tablas Mas Utilizadas')
    axes[0,1].set_xlabel('Numero de SPs Usuarios')
    
    # 3. Top 10 tablas más generadas
    tablas_gen = [(nombre, tabla['estadisticas']['total_sps_generadores']) 
                  for nombre, tabla in tablas.items() if tabla['estadisticas']['total_sps_generadores'] > 0]
    tablas_gen.sort(key=lambda x: x[1], reverse=True)
    top_10_gen = tablas_gen[:10]
    
    nombres_gen = [x[0][:30] + '...' if len(x[0]) > 30 else x[0] for x in top_10_gen]
    generaciones = [x[1] for x in top_10_gen]
    
    axes[1,0].barh(nombres_gen, generaciones, color='lightcoral')
    axes[1,0].set_title('Top 10 Tablas Mas Generadas')
    axes[1,0].set_xlabel('Numero de SPs Generadores')
    
    # 4. Distribución de uso de tablas
    axes[1,1].hist(uso_tablas, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
    axes[1,1].set_title('Distribucion de Uso de Tablas')
    axes[1,1].set_xlabel('Numero de SPs Usuarios')
    axes[1,1].set_ylabel('Frecuencia')
    axes[1,1].axvline(np.mean(uso_tablas), color='red', linestyle='--', label=f'Media: {np.mean(uso_tablas):.1f}')
    axes[1,1].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '01_analisis_general.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    return metadata, tablas_uso, tablas_gen

def analizar_sps_complejidad(data, output_dir):
    """Analizar complejidad de los stored procedures"""
    print("🔍 Analizando complejidad de SPs...")
    
    # Recopilar todos los SPs
    todos_sps = []
    sps_vistos = set()
    
    for tabla_nombre, tabla_info in data['tablas'].items():
        # SPs generadores
        for sp in tabla_info['sps_generadores']:
            if sp['nombre_sp'] not in sps_vistos:
                sps_vistos.add(sp['nombre_sp'])
                todos_sps.append({
                    'nombre': sp['nombre_sp'],
                    'tipo': 'generador',
                    'tablas_generadas': len(sp['tablas_generadas']),
                    'tablas_utilizadas': len(sp['tablas_utilizadas']),
                    'inputs_count': sp['metadata']['inputs_count'],
                    'outputs_count': sp['metadata']['outputs_count'],
                    'creates_tables': sp['metadata']['creates_tables']
                })
        
        # SPs usuarios
        for sp in tabla_info['sps_usuarios']:
            if sp['nombre_sp'] not in sps_vistos:
                sps_vistos.add(sp['nombre_sp'])
                todos_sps.append({
                    'nombre': sp['nombre_sp'],
                    'tipo': 'usuario',
                    'tablas_generadas': len(sp['tablas_generadas']),
                    'tablas_utilizadas': len(sp['tablas_utilizadas']),
                    'inputs_count': sp['metadata']['inputs_count'],
                    'outputs_count': sp['metadata']['outputs_count'],
                    'creates_tables': sp['metadata']['creates_tables']
                })
    
    df_sps = pd.DataFrame(todos_sps)
    
    # Gráficos de complejidad
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('ANALISIS DE COMPLEJIDAD DE STORED PROCEDURES', fontsize=16, fontweight='bold')
    
    # 1. Distribución de inputs vs outputs
    if not df_sps.empty:
        scatter = axes[0,0].scatter(df_sps['inputs_count'], df_sps['outputs_count'], 
                                   c=df_sps['tablas_utilizadas'], alpha=0.6, cmap='viridis')
        axes[0,0].set_xlabel('Numero de Inputs')
        axes[0,0].set_ylabel('Numero de Outputs')
        axes[0,0].set_title('Inputs vs Outputs por SP')
        plt.colorbar(scatter, ax=axes[0,0], label='Tablas Utilizadas')
        
        # 2. Top SPs más complejos (por inputs)
        top_complejos = df_sps.nlargest(10, 'inputs_count')[['nombre', 'inputs_count', 'outputs_count']]
        top_complejos['nombre_corto'] = top_complejos['nombre'].str[:25] + '...'
        
        x = range(len(top_complejos))
        width = 0.35
        axes[0,1].bar([i - width/2 for i in x], top_complejos['inputs_count'], width, label='Inputs', alpha=0.7)
        axes[0,1].bar([i + width/2 for i in x], top_complejos['outputs_count'], width, label='Outputs', alpha=0.7)
        axes[0,1].set_xlabel('Stored Procedures')
        axes[0,1].set_ylabel('Cantidad')
        axes[0,1].set_title('Top 10 SPs Mas Complejos')
        axes[0,1].set_xticks(x)
        axes[0,1].set_xticklabels(top_complejos['nombre_corto'], rotation=45, ha='right')
        axes[0,1].legend()
        
        # 3. Distribución de tipos de SP
        tipo_counts = df_sps['tipo'].value_counts()
        axes[1,0].pie(tipo_counts.values, labels=tipo_counts.index, autopct='%1.1f%%', startangle=90)
        axes[1,0].set_title('Distribucion de Tipos de SP')
        
        # 4. SPs que crean tablas
        crea_tablas = df_sps['creates_tables'].value_counts()
        axes[1,1].bar(['No crea tablas', 'Crea tablas'], crea_tablas.values, color=['lightcoral', 'lightgreen'])
        axes[1,1].set_title('SPs que Crean Tablas')
        axes[1,1].set_ylabel('Cantidad')
        
        for i, v in enumerate(crea_tablas.values):
            axes[1,1].text(i, v + 0.1, str(v), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '02_complejidad_sps.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    return df_sps

def crear_grafo_dependencias(data, output_dir):
    """Crear grafo de dependencias entre tablas y SPs"""
    print("🕸️ Creando grafo de dependencias...")
    
    G = nx.DiGraph()
    
    # Agregar nodos y aristas
    for tabla_nombre, tabla_info in data['tablas'].items():
        G.add_node(tabla_nombre, node_type='tabla', tipo=tabla_info['tipo'])
        
        # SPs generadores (tablas utilizadas → SP → tablas generadas)
        for sp in tabla_info['sps_generadores']:
            sp_nombre = sp['nombre_sp']
            G.add_node(sp_nombre, node_type='sp', tipo='generador')
            
            # Conectar tablas utilizadas al SP
            for tabla_utilizada in sp['tablas_utilizadas']:
                G.add_edge(tabla_utilizada, sp_nombre, relationship='usa')
            
            # Conectar SP a tablas generadas
            for tabla_generada in sp['tablas_generadas']:
                G.add_edge(sp_nombre, tabla_generada, relationship='genera')
        
        # SPs usuarios (SP → tablas utilizadas)
        for sp in tabla_info['sps_usuarios']:
            sp_nombre = sp['nombre_sp']
            G.add_node(sp_nombre, node_type='sp', tipo='usuario')
            
            # Conectar SP a tablas utilizadas
            for tabla_utilizada in sp['tablas_utilizadas']:
                G.add_edge(sp_nombre, tabla_utilizada, relationship='usa')
    
    # Análisis del grafo
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('ANALISIS DE RED DE DEPENDENCIAS', fontsize=16, fontweight='bold')
    
    # 1. Distribución de grados (conexiones)
    if len(G) > 0:
        grados = [d for n, d in G.degree()]
        axes[0,0].hist(grados, bins=30, alpha=0.7, color='lightblue', edgecolor='black')
        axes[0,0].set_title('Distribucion de Conexiones por Nodo')
        axes[0,0].set_xlabel('Numero de Conexiones')
        axes[0,0].set_ylabel('Frecuencia')
        axes[0,0].axvline(np.mean(grados), color='red', linestyle='--', label=f'Media: {np.mean(grados):.1f}')
        axes[0,0].legend()
        
        # 2. Top nodos más conectados
        grado_centralidad = nx.degree_centrality(G)
        top_conectados = sorted(grado_centralidad.items(), key=lambda x: x[1], reverse=True)[:10]
        
        nombres = [x[0][:25] + '...' if len(x[0]) > 25 else x[0] for x in top_conectados]
        centralidades = [x[1] for x in top_conectados]
        
        axes[0,1].barh(nombres, centralidades, color='lightgreen')
        axes[0,1].set_title('Top 10 Nodos Mas Conectados')
        axes[0,1].set_xlabel('Centralidad de Grado')
        
        # 3. Componentes conectados
        componentes = list(nx.weakly_connected_components(G))
        tam_componentes = [len(comp) for comp in componentes]
        
        axes[1,0].bar(range(1, min(11, len(tam_componentes) + 1)), 
                      tam_componentes[:10], color='orange', alpha=0.7)
        axes[1,0].set_title('Tamaño de Componentes Conectados (Top 10)')
        axes[1,0].set_xlabel('Componente')
        axes[1,0].set_ylabel('Numero de Nodos')
        
        # 4. Distribución de tipos de nodos
        tipos_nodo = [data.get('node_type', 'desconocido') for n, data in G.nodes(data=True)]
        tipo_counts = pd.Series(tipos_nodo).value_counts()
        
        axes[1,1].pie(tipo_counts.values, labels=tipo_counts.index, autopct='%1.1f%%', startangle=90)
        axes[1,1].set_title('Distribucion de Tipos de Nodos')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '03_analisis_red.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Guardar datos del grafo para análisis posterior
    if len(G) > 0:
        nx.write_gexf(G, os.path.join(output_dir, 'grafo_dependencias.gexf'))
        return G, grado_centralidad
    else:
        return None, {}

def analizar_patrones_tablas(data, output_dir):
    """Analizar patrones en nombres de tablas"""
    print("🎯 Analizando patrones en nombres de tablas...")
    
    nombres_tablas = list(data['tablas'].keys())
    
    # Extraer prefijos
    prefijos = []
    for nombre in nombres_tablas:
        if '_' in nombre:
            prefijo = nombre.split('_')[0]
            prefijos.append(prefijo)
    
    prefijo_counts = Counter(prefijos)
    
    # Analizar dominios funcionales
    dominios = {
        'VENTA': ['venta', 'pedido', 'liquidado'],
        'CLIENTE': ['cliente', 'cartera'],
        'PRODUCTO': ['producto', 'inventario'],
        'PROGRAMACION': ['programacion', 'visita'],
        'REPORTE': ['reporte', 'avance'],
        'TEMPORAL': ['xtmp', 'tmp'],
        'FUERZA_VENTA': ['fuerza_venta', 'vendedor', 'supervisor'],
        'CIUDAD': ['ciudad', 'ruta']
    }
    
    dominio_counts = defaultdict(int)
    for nombre in nombres_tablas:
        nombre_lower = nombre.lower()
        for dominio, palabras in dominios.items():
            if any(palabra in nombre_lower for palabra in palabras):
                dominio_counts[dominio] += 1
                break
        else:
            dominio_counts['OTROS'] += 1
    
    # Gráficos de patrones
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('ANALISIS DE PATRONES Y DOMINIOS', fontsize=16, fontweight='bold')
    
    # 1. Prefijos más comunes
    top_prefijos = prefijo_counts.most_common(10)
    prefijos_nombres = [x[0] for x in top_prefijos]
    prefijos_counts = [x[1] for x in top_prefijos]
    
    axes[0,0].bar(prefijos_nombres, prefijos_counts, color='lightseagreen')
    axes[0,0].set_title('Top 10 Prefijos de Tablas')
    axes[0,0].set_ylabel('Cantidad')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    # 2. Dominios funcionales
    dominio_items = sorted(dominio_counts.items(), key=lambda x: x[1], reverse=True)
    dominio_nombres = [x[0] for x in dominio_items]
    dominio_valores = [x[1] for x in dominio_items]
    
    axes[0,1].bar(dominio_nombres, dominio_valores, color='coral')
    axes[0,1].set_title('Distribucion por Dominios Funcionales')
    axes[0,1].set_ylabel('Cantidad de Tablas')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    # 3. Tablas temporales vs permanentes
    tipos_tabla = [tabla['tipo'] for tabla in data['tablas'].values()]
    tipo_counts = pd.Series(tipos_tabla).value_counts()
    
    axes[1,0].pie(tipo_counts.values, labels=tipo_counts.index, autopct='%1.1f%%', startangle=90)
    axes[1,0].set_title('Tablas Temporales vs Permanentes')
    
    # 4. Longitud de nombres de tablas
    longitudes = [len(nombre) for nombre in nombres_tablas]
    axes[1,1].hist(longitudes, bins=20, alpha=0.7, color='purple', edgecolor='black')
    axes[1,1].set_title('Distribucion de Longitud de Nombres')
    axes[1,1].set_xlabel('Longitud del Nombre')
    axes[1,1].set_ylabel('Frecuencia')
    axes[1,1].axvline(np.mean(longitudes), color='red', linestyle='--', 
                     label=f'Media: {np.mean(longitudes):.1f}')
    axes[1,1].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '04_patrones_tablas.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    return prefijo_counts, dominio_counts

def generar_reporte_insights(data, metadata, df_sps, G, grado_centralidad, output_dir):
    """Generar reporte de insights en texto"""
    print("📝 Generando reporte de insights...")
    
    insights = []
    insights.append("=" * 80)
    insights.append("REPORTE DE INSIGHTS - SISTEMA DE TRAZABILIDAD (V7)")
    insights.append("=" * 80)
    insights.append("")
    
    # Insights generales
    insights.append("INSIGHTS GENERALES:")
    insights.append(f"• Total de tablas: {metadata['total_tablas']}")
    insights.append(f"• Total de SPs: {metadata['total_sps']}")
    insights.append(f"• Tablas con generadores: {metadata['tablas_con_generadores']}")
    insights.append(f"• Tablas origen: {metadata['tablas_origen']}")
    insights.append("")
    
    # Tablas críticas
    insights.append("TABLAS CRITICAS (Alto impacto):")
    tablas_uso = [(nombre, tabla['estadisticas']['total_sps_usuarios']) 
                  for nombre, tabla in data['tablas'].items()]
    tablas_uso.sort(key=lambda x: x[1], reverse=True)
    
    for i, (nombre, uso) in enumerate(tablas_uso[:5], 1):
        insights.append(f"  {i}. {nombre} -> {uso} SPs usuarios")
    insights.append("")
    
    # SPs más complejos
    insights.append("SPs MAS COMPLEJOS:")
    if not df_sps.empty:
        sps_complejos = df_sps.nlargest(5, 'inputs_count')[['nombre', 'inputs_count', 'outputs_count']]
        for i, row in sps_complejos.iterrows():
            insights.append(f"  • {row['nombre']} -> {row['inputs_count']} inputs, {row['outputs_count']} outputs")
    insights.append("")
    
    # Nodos más centrales
    insights.append("NODOS MAS CENTRALES EN LA RED:")
    if grado_centralidad:
        top_centrales = sorted(grado_centralidad.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (nodo, centralidad) in enumerate(top_centrales, 1):
            node_type = G.nodes[nodo].get('node_type', 'desconocido') if G else 'desconocido'
            tipo = "TABLA" if node_type == 'tabla' else "SP"
            insights.append(f"  {i}. {nodo} [{tipo}] -> Centralidad: {centralidad:.3f}")
    insights.append("")
    
    # Riesgos y recomendaciones
    insights.append("RIESGOS IDENTIFICADOS:")
    
    # Tablas con muchos usuarios (puntos únicos de fallo)
    tablas_sobreutilizadas = [nombre for nombre, uso in tablas_uso if uso > 20]
    if tablas_sobreutilizadas:
        insights.append("• Puntos unicos de fallo:")
        for tabla in tablas_sobreutilizadas[:3]:
            insights.append(f"  - {tabla} (demasiadas dependencias)")
    
    # SPs muy complejos
    if not df_sps.empty:
        sps_muy_complejos = df_sps[df_sps['inputs_count'] > 8]
        if not sps_muy_complejos.empty:
            insights.append("• SPs demasiado complejos:")
            for _, sp in sps_muy_complejos.head(3).iterrows():
                insights.append(f"  - {sp['nombre']} ({sp['inputs_count']} inputs)")
    
    insights.append("")
    insights.append("RECOMENDACIONES:")
    insights.append("1. Considerar refactorizacion de tablas sobreutilizadas")
    insights.append("2. Revisar SPs con alta complejidad para posibles divisiones")
    insights.append("3. Monitorear dependencias de tablas criticas")
    
    # Guardar reporte
    with open(os.path.join(output_dir, 'reporte_insights.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(insights))
    
    # Imprimir resumen en consola
    print("\n" + "=" * 60)
    print("RESUMEN DE INSIGHTS PRINCIPALES")
    print("=" * 60)
    for insight in insights[:20]:
        print(insight)

def main():
    """Función principal"""
    print("INICIANDO ANALISIS EXPLORATORIO DE TRAZABILIDAD (V7)")
    print("=" * 60)
    
    # Crear carpeta de resultados
    output_dir = preparar_carpeta_salida()
    print(f"📁 Resultados se guardaran en: {output_dir}")
    
    # Cargar datos
    data = cargar_datos()
    if not data:
        return
    
    # Ejecutar análisis
    try:
        metadata, tablas_uso, tablas_gen = analisis_general_sistema(data, output_dir)
        df_sps = analizar_sps_complejidad(data, output_dir)
        G, grado_centralidad = crear_grafo_dependencias(data, output_dir)
        prefijo_counts, dominio_counts = analizar_patrones_tablas(data, output_dir)
        generar_reporte_insights(data, metadata, df_sps, G, grado_centralidad, output_dir)
        
        print("\n✅ ANALISIS COMPLETADO EXITOSAMENTE!")
        print(f"📊 Graficos guardados en: {output_dir}")
        
    except Exception as e:
        print(f"❌ Error durante el analisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
