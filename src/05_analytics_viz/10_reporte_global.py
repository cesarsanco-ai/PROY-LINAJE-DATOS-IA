#antes: 6_3_reporte_global_sistema.py

# src/05_analytics_viz/10_reporte_global.py
import pandas as pd
import json
import os
import sys
from collections import defaultdict, deque
from datetime import datetime

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
from config_paths import KNOWLEDGE_DIR, PROCESSED_DIR, GOLD_DIR

class GeneradorMaestroTrazabilidad:
    def __init__(self):
        self.metadata_sp = None
        self.maestro_tablas = None
        self.maestro_sp = None
        # Usamos la ruta GOLD para guardar los resultados finales
        self.resultados_dir = GOLD_DIR
        
        # Crear directorio de resultados si no existe (aunque config_paths ya lo hace)
        os.makedirs(self.resultados_dir, exist_ok=True)
    
    def cargar_datos(self):
        """Carga todos los datos necesarios desde las capas correctas"""
        try:
            print("📂 Cargando datos del sistema...")
            
            # Metadata de SPs con IA (Capa Knowledge)
            path_meta = os.path.join(KNOWLEDGE_DIR, "banco_metadata_sp.json")
            with open(path_meta, 'r', encoding='utf-8') as f:
                self.metadata_sp = json.load(f)
            
            # Maestros (Capa Processed)
            path_tablas = os.path.join(PROCESSED_DIR, "maestro_tablas.csv")
            path_sp = os.path.join(PROCESSED_DIR, "maestro_sp.csv")
            
            self.maestro_tablas = pd.read_csv(path_tablas)
            self.maestro_sp = pd.read_csv(path_sp)
            
            print("✅ Datos cargados correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def clasificar_sps(self):
        """Clasifica SPs en generadores y usuarios"""
        sps_clasificados = {}
        
        for sp in self.metadata_sp:
            sp_id = sp['id_sp']
            outputs = sp.get('outputs', [])
            inputs = sp.get('inputs', [])
            
            # Convertir IDs a nombres de tablas
            outputs_nombres = []
            for output_id in outputs:
                tabla_nombre = self.obtener_nombre_tabla_por_id(output_id)
                if tabla_nombre:
                    outputs_nombres.append(tabla_nombre)
            
            inputs_nombres = []
            for input_id in inputs:
                tabla_nombre = self.obtener_nombre_tabla_por_id(input_id)
                if tabla_nombre:
                    inputs_nombres.append(tabla_nombre)
            
            # Clasificar SP
            if outputs_nombres:
                tipo_sp = "generador"
            else:
                tipo_sp = "usuario"
            
            sps_clasificados[sp_id] = {
                'id_sp': sp_id,
                'nombre_sp': sp.get('nombre_sp', ''),
                'tipo_sp': tipo_sp,
                'tablas_generadas': outputs_nombres,
                'tablas_utilizadas': inputs_nombres,
                'metadata': {
                    'external_sources': sp.get('external_sources', False),
                    'creates_tables': sp.get('creates_tables', False),
                    'ai_review': sp.get('ai_review', False),
                    'inputs_count': len(inputs_nombres),
                    'outputs_count': len(outputs_nombres)
                }
            }
        
        return sps_clasificados
    
    def obtener_nombre_tabla_por_id(self, tabla_id):
        """Obtiene el nombre de tabla por ID"""
        if not hasattr(self, 'mapeo_id_a_nombre'):
            self.mapeo_id_a_nombre = dict(zip(
                self.maestro_tablas['id_tabla'], 
                self.maestro_tablas['nombre_tabla']
            ))
        return self.mapeo_id_a_nombre.get(tabla_id, tabla_id)
    
    def construir_maestro_tablas(self, sps_clasificados):
        """Construye el maestro completo de tablas"""
        maestro_tablas = {}
        
        # Primera pasada: identificar todas las tablas
        todas_las_tablas = set(self.maestro_tablas['nombre_tabla'])
        
        for tabla_nombre in todas_las_tablas:
            tabla_id = self.obtener_id_tabla_por_nombre(tabla_nombre)
            
            # Encontrar SPs generadores de esta tabla
            sps_generadores = []
            sps_usuarios = []
            
            for sp_id, sp_info in sps_clasificados.items():
                if tabla_nombre in sp_info['tablas_generadas']:
                    sps_generadores.append(sp_info)
                elif tabla_nombre in sp_info['tablas_utilizadas']:
                    sps_usuarios.append(sp_info)
            
            # Determinar tipo de tabla
            if sps_generadores:
                tipo_tabla = "generada"
            else:
                tipo_tabla = "origen"
            
            # Estadísticas
            estadisticas = {
                'total_sps_generadores': len(sps_generadores),
                'total_sps_usuarios': len(sps_usuarios),
                'sps_con_fuentes_externas': len([sp for sp in sps_generadores if sp['metadata']['external_sources']]),
                'sps_creadores_tablas': len([sp for sp in sps_generadores if sp['metadata']['creates_tables']])
            }
            
            maestro_tablas[tabla_nombre] = {
                'id_tabla': tabla_id,
                'tipo': tipo_tabla,
                'estadisticas': estadisticas,
                'sps_generadores': sps_generadores,
                'sps_usuarios': sps_usuarios
            }
        
        return maestro_tablas
    
    def obtener_id_tabla_por_nombre(self, tabla_nombre):
        """Obtiene el ID de tabla por nombre"""
        if not hasattr(self, 'mapeo_nombre_a_id'):
            self.mapeo_nombre_a_id = dict(zip(
                self.maestro_tablas['nombre_tabla'], 
                self.maestro_tablas['id_tabla']
            ))
        return self.mapeo_nombre_a_id.get(tabla_nombre, f"T_{tabla_nombre[:10]}")
    
    def generar_maestro_completo(self):
        """Genera el maestro completo de trazabilidad"""
        if not self.cargar_datos():
            return None
        
        print("🔍 Clasificando SPs...")
        sps_clasificados = self.clasificar_sps()
        
        print("🏗️ Construyendo maestro de tablas...")
        maestro_tablas = self.construir_maestro_tablas(sps_clasificados)
        
        print("📊 Calculando estadísticas...")
        estadisticas_globales = self.calcular_estadisticas_globales(maestro_tablas, sps_clasificados)
        
        maestro_completo = {
            'metadata': estadisticas_globales,
            'tablas': maestro_tablas,
            'sps': sps_clasificados,
            'dependencias': self.analizar_dependencias(maestro_tablas)
        }
        
        return maestro_completo
    
    def calcular_estadisticas_globales(self, maestro_tablas, sps_clasificados):
        """Calcula estadísticas globales del sistema"""
        total_tablas = len(maestro_tablas)
        tablas_con_generadores = len([t for t in maestro_tablas.values() if t['tipo'] == 'generada'])
        tablas_origen = total_tablas - tablas_con_generadores
        
        total_sps = len(sps_clasificados)
        sps_generadores = len([s for s in sps_clasificados.values() if s['tipo_sp'] == 'generador'])
        sps_usuarios = total_sps - sps_generadores
        
        return {
            'fecha_generacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_tablas': total_tablas,
            'total_sps': total_sps,
            'tablas_con_generadores': tablas_con_generadores,
            'tablas_origen': tablas_origen,
            'sps_generadores': sps_generadores,
            'sps_usuarios': sps_usuarios
        }
    
    def analizar_dependencias(self, maestro_tablas):
        """Analiza las dependencias y complejidad del sistema"""
        # Implementar análisis de profundidad y rutas críticas
        return {
            'por_profundidad': {},
            'red_compleja': {}
        }
    
    def guardar_maestro_json(self, maestro, archivo_salida="maestro_trazabilidad_completo.json"):
        """Guarda el maestro en un archivo JSON"""
        try:
            ruta_completa = os.path.join(self.resultados_dir, archivo_salida)
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                json.dump(maestro, f, indent=2, ensure_ascii=False)
            return ruta_completa
        except Exception as e:
            print(f"❌ Error guardando maestro JSON: {e}")
            return None
    
    def generar_reporte_texto(self, maestro, archivo_salida="output_trazabilidad.txt"):
        """Genera un reporte en texto plano con la información más importante"""
        try:
            ruta_completa = os.path.join(self.resultados_dir, archivo_salida)
            
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                # Encabezado
                f.write("=" * 80 + "\n")
                f.write("REPORTE DE TRAZABILIDAD - SISTEMA COMPLETO (V7)\n")
                f.write("=" * 80 + "\n\n")
                
                # Estadísticas globales
                metadata = maestro['metadata']
                f.write("📊 ESTADÍSTICAS GLOBALES:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Fecha de generación: {metadata['fecha_generacion']}\n")
                f.write(f"Total tablas en el sistema: {metadata['total_tablas']}\n")
                f.write(f"Total SPs analizados: {metadata['total_sps']}\n")
                f.write(f"Tablas con generadores: {metadata['tablas_con_generadores']}\n")
                f.write(f"Tablas origen: {metadata['tablas_origen']}\n")
                f.write(f"SPs generadores: {metadata['sps_generadores']}\n")
                f.write(f"SPs usuarios: {metadata['sps_usuarios']}\n\n")
                
                # Top 10 tablas más complejas
                f.write("🏆 TOP 10 TABLAS MÁS COMPLEJAS:\n")
                f.write("-" * 40 + "\n")
                
                tablas_complejas = []
                for tabla_nombre, info in maestro['tablas'].items():
                    if info['tipo'] == 'generada':
                        complejidad = info['estadisticas']['total_sps_generadores']
                        tablas_complejas.append((tabla_nombre, complejidad, info['id_tabla']))
                
                tablas_complejas.sort(key=lambda x: x[1], reverse=True)
                
                for i, (tabla, complejidad, tabla_id) in enumerate(tablas_complejas[:10], 1):
                    f.write(f"{i:2d}. {tabla} ({tabla_id})\n")
                    f.write(f"    SPs generadores: {complejidad}\n")
                    f.write(f"    SPs usuarios: {maestro['tablas'][tabla]['estadisticas']['total_sps_usuarios']}\n")
                    f.write(f"    Fuentes externas: {maestro['tablas'][tabla]['estadisticas']['sps_con_fuentes_externas']}\n\n")
                
                # SPs más críticos
                f.write("⚠️  SPs MÁS CRÍTICOS (con fuentes externas):\n")
                f.write("-" * 40 + "\n")
                
                sps_criticos = []
                for sp_id, sp_info in maestro['sps'].items():
                    if sp_info['metadata']['external_sources']:
                        sps_criticos.append((
                            sp_info['nombre_sp'], 
                            sp_id,
                            len(sp_info['tablas_generadas']),
                            len(sp_info['tablas_utilizadas'])
                        ))
                
                for i, (sp_nombre, sp_id, outputs, inputs) in enumerate(sps_criticos[:10], 1):
                    f.write(f"{i:2d}. {sp_nombre} ({sp_id})\n")
                    f.write(f"    Tablas generadas: {outputs}\n")
                    f.write(f"    Tablas utilizadas: {inputs}\n\n")
                
                # Tablas origen principales
                f.write("🏁 PRINCIPALES TABLAS ORIGEN:\n")
                f.write("-" * 40 + "\n")
                
                tablas_origen = []
                for tabla_nombre, info in maestro['tablas'].items():
                    if info['tipo'] == 'origen' and info['estadisticas']['total_sps_usuarios'] > 0:
                        tablas_origen.append((
                            tabla_nombre,
                            info['id_tabla'],
                            info['estadisticas']['total_sps_usuarios']
                        ))
                
                tablas_origen.sort(key=lambda x: x[2], reverse=True)
                
                for i, (tabla, tabla_id, usuarios) in enumerate(tablas_origen[:15], 1):
                    f.write(f"{i:2d}. {tabla} ({tabla_id}) - Usada por {usuarios} SPs\n")
            
            return ruta_completa
            
        except Exception as e:
            print(f"❌ Error generando reporte texto: {e}")
            return None
    
    def mostrar_resumen_terminal(self, maestro, ruta_json, ruta_txt):
        """Muestra un resumen breve en terminal"""
        metadata = maestro['metadata']
        
        print(f"\n{'='*60}")
        print("✅ GENERACIÓN DE MAESTRO COMPLETADA")
        print(f"{'='*60}")
        print(f"📊 RESUMEN DEL SISTEMA:")
        print(f"   • Tablas totales: {metadata['total_tablas']}")
        print(f"   • SPs analizados: {metadata['total_sps']}")
        print(f"   • Tablas con generadores: {metadata['tablas_con_generadores']}")
        print(f"   • Tablas origen: {metadata['tablas_origen']}")
        print(f"   • SPs generadores: {metadata['sps_generadores']}")
        print(f"   • SPs usuarios: {metadata['sps_usuarios']}")
        
        # Top 3 tablas más complejas
        tablas_complejas = []
        for tabla_nombre, info in maestro['tablas'].items():
            if info['tipo'] == 'generada':
                complejidad = info['estadisticas']['total_sps_generadores']
                tablas_complejas.append((tabla_nombre, complejidad))
        
        tablas_complejas.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n🏆 TABLAS MÁS COMPLEJAS:")
        for tabla, complejidad in tablas_complejas[:3]:
            print(f"   • {tabla}: {complejidad} SPs generadores")
        
        print(f"\n💾 RESULTADOS GUARDADOS EN:")
        print(f"   📄 JSON completo: {ruta_json}")
        print(f"   📝 Reporte texto: {ruta_txt}")
        print(f"{'='*60}")

def main():
    print("🏗️ GENERADOR DE MAESTRO DE TRAZABILIDAD (V7)")
    print("=" * 50)
    
    generador = GeneradorMaestroTrazabilidad()
    maestro = generador.generar_maestro_completo()
    
    if maestro:
        # Guardar archivos
        ruta_json = generador.guardar_maestro_json(maestro)
        ruta_txt = generador.generar_reporte_texto(maestro)
        
        if ruta_json and ruta_txt:
            # Mostrar solo resumen en terminal
            generador.mostrar_resumen_terminal(maestro, ruta_json, ruta_txt)
        else:
            print("❌ Error guardando los archivos de resultados")
    else:
        print("❌ Error generando el maestro")

if __name__ == "__main__":
    main()