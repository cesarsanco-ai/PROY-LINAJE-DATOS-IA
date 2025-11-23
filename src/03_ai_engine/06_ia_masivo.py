# antes: 4_9_barrido_masivo_metadata.py

# actual: src/03_ai_engine/06_ia_masivo.py
import json
import os
import sys
from openai import OpenAI

# ==============================================
# 1. CONFIGURACIÓN DE RUTAS (NUEVO)
# ==============================================
# Obtenemos la ruta de este script (src/03_ai_engine/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para llegar a 'src/'
src_dir = os.path.dirname(current_dir)
# Agregamos 'src' al path para importar config_paths
sys.path.append(src_dir)

# Importamos las rutas maestras
from config_paths import PROCESSED_DIR, KNOWLEDGE_DIR, API_KEY_FILE

# Rutas de archivos específicos
FILE_MAESTRO_SP = os.path.join(PROCESSED_DIR, "maestro_sp.json")
FILE_METADATA_SP = os.path.join(KNOWLEDGE_DIR, "banco_metadata_sp.json")

def cargar_api_key():
    """Carga la API key desde archivo"""
    try:
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def cargar_maestro_sp():
    """
    Carga todo el maestro_sp.json
    """
    try:
        with open(FILE_MAESTRO_SP, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró {FILE_MAESTRO_SP}")
        return None
    except Exception as e:
        print(f"❌ Error cargando maestro_sp: {e}")
        return None

def cargar_metadata_existente():
    """
    Carga el banco_metadata_sp.json existente
    """
    if os.path.exists(FILE_METADATA_SP):
        try:
            with open(FILE_METADATA_SP, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error cargando metadata existente: {e}")
            return []
    else:
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        return []

def obtener_sps_no_analizados(maestro_sp, metadata_existente):
    """
    Retorna los SPs que no tienen ai_review=true en la metadata
    """
    sps_analizados = set()
    
    # Obtener IDs de SPs ya analizados
    for sp_meta in metadata_existente:
        if sp_meta.get('ai_review') == True:
            sps_analizados.add(sp_meta['id_sp'].lower())
    
    # Filtrar SPs no analizados
    sps_no_analizados = []
    for sp in maestro_sp:
        if sp['id_sp'].lower() not in sps_analizados:
            sps_no_analizados.append({
                'id_sp': sp['id_sp'],
                'nombre_sp': sp['nombre_sp'],
                'codigo_sql': sp['codigo_sql']
            })
    
    return sps_no_analizados

def extraer_metadata_sp(codigo_sql, nombre_sp):
    """
    Extrae metadata de un SP usando IA
    """
    api_key = cargar_api_key()
    if not api_key:
        return {"error": "No se encontró API key"}
    
    client = OpenAI(api_key=api_key)
    
    # PROMPT OPTIMIZADO para extracción estructurada
    prompt_sistema = """
    Eres un especialista en análisis de código SQL Server. 
    Extrae EXCLUSIVAMENTE la siguiente información del stored procedure:

    1. TABLAS DE ENTRADA (inputs): Tablas que se LEEN (FROM, JOIN, subqueries)
    2. TABLAS DE SALIDA (outputs): Tablas que se ESCRIBEN (INSERT, UPDATE, CREATE, DELETE)
    3. EXTERNAL_SOURCES: True si detectas BULK INSERT, OPENROWSET, OPENQUERY, o carga desde archivos externos
    4. CREATES_TABLES: True si crea tablas (temporales o permanentes) con CREATE TABLE

    Responde SOLO con un JSON válido, sin explicaciones adicionales.
    Nombres de tablas exactos como aparecen en el código.
    """
    
    prompt_usuario = f"""
    Analiza este stored procedure y extrae la metadata:

    NOMBRE_SP: {nombre_sp}
    
    CÓDIGO_SQL:
    ```sql
    {codigo_sql[:12000]}  # Limitar tokens para costo
    ```

    Formato de respuesta requerido (JSON válido):
    {{
        "inputs": ["tabla1", "tabla2"],
        "outputs": ["tabla3"],
        "external_sources": false,
        "creates_tables": true
    }}
    """
    
    try:
        print("🔄 Enviando a IA para análisis...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0,
            max_tokens=800
        )
        
        # Parsear respuesta JSON
        respuesta_texto = response.choices[0].message.content
        
        # Limpiar respuesta (quitar markdown code blocks si existen)
        respuesta_texto = respuesta_texto.replace('```json', '').replace('```', '').strip()
        
        metadata = json.loads(respuesta_texto)
        
        return metadata
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON de IA: {e}")
        print(f"📄 Respuesta cruda: {respuesta_texto}")
        return {"error": f"Error parseando JSON: {e}", "respuesta_cruda": respuesta_texto}
    except Exception as e:
        return {"error": f"Error API: {str(e)}"}

def guardar_metadata_completa(metadata_completo):
    """
    Guarda toda la metadata en el banco_metadata_sp.json
    """
    try:
        with open(FILE_METADATA_SP, 'w', encoding='utf-8') as f:
            json.dump(metadata_completo, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Metadata guardada en {FILE_METADATA_SP}")
        return True
        
    except Exception as e:
        print(f"❌ Error guardando metadata: {e}")
        return False

def procesar_sp_batch():
    """
    Función principal: procesa SPs no analizados en lote
    """
    print("🔍 EXTRACTOR IA DE METADATA - PROCESAMIENTO POR LOTES (V7)")
    print("=" * 60)
    
    # 1. Cargar datos
    print("📂 Cargando datos...")
    maestro_sp = cargar_maestro_sp()
    if not maestro_sp:
        return
    
    metadata_existente = cargar_metadata_existente()
    
    # 2. Obtener SPs no analizados
    sps_no_analizados = obtener_sps_no_analizados(maestro_sp, metadata_existente)
    
    if not sps_no_analizados:
        print("✅ Todos los SPs ya han sido analizados (ai_review=true)")
        return
    
    print(f"📊 SPs encontrados: {len(maestro_sp)}")
    print(f"🔍 SPs no analizados: {len(sps_no_analizados)}")
    
    # 3. Seleccionar modo de procesamiento
    print(f"\n🎯 MODOS DE PROCESAMIENTO:")
    print("   X - Procesar primeros 5 SPs (Prueba)")
    print("   Z - Procesar TODOS los SPs no analizados")
    
    modo = input("📝 Selecciona modo (X/Z): ").strip().upper()
    
    if modo == 'X':
        sps_a_procesar = sps_no_analizados[:5]
    elif modo == 'Z':
        sps_a_procesar = sps_no_analizados
    else:
        print("❌ Modo no válido")
        return
    
    print(f"\n🚀 Procesando {len(sps_a_procesar)} SPs...")
    
    # 4. Procesar cada SP
    procesados_exitosos = 0
    procesados_con_error = 0
    
    for i, sp_info in enumerate(sps_a_procesar, 1):
        print(f"\n{'='*50}")
        print(f"📋 SP {i}/{len(sps_a_procesar)}: {sp_info['nombre_sp']} ({sp_info['id_sp']})")
        print(f"📏 Longitud del código: {len(sp_info['codigo_sql'])} caracteres")
        
        # Extraer metadata con IA
        metadata = extraer_metadata_sp(sp_info['codigo_sql'], sp_info['nombre_sp'])
        
        # Actualizar metadata existente
        if "error" not in metadata:
            # Buscar si ya existe este SP en metadata
            encontrado = False
            for sp_meta in metadata_existente:
                if sp_meta['id_sp'].lower() == sp_info['id_sp'].lower():
                    sp_meta.update({
                        "nombre_sp": sp_info['nombre_sp'],
                        "inputs": metadata.get("inputs", []),
                        "outputs": metadata.get("outputs", []),
                        "external_sources": metadata.get("external_sources", False),
                        "creates_tables": metadata.get("creates_tables", False),
                        "ai_review": True
                    })
                    encontrado = True
                    break
            
            # Si no existe, agregar nuevo
            if not encontrado:
                metadata_existente.append({
                    "id_sp": sp_info['id_sp'].lower(),
                    "nombre_sp": sp_info['nombre_sp'],
                    "inputs": metadata.get("inputs", []),
                    "outputs": metadata.get("outputs", []),
                    "external_sources": metadata.get("external_sources", False),
                    "creates_tables": metadata.get("creates_tables", False),
                    "ai_review": True
                })
            
            procesados_exitosos += 1
            print(f"✅ Analizado exitosamente")
            
            # Mostrar resumen
            print(f"📥 INPUTS: {len(metadata.get('inputs', []))}")
            print(f"📤 OUTPUTS: {len(metadata.get('outputs', []))}")
            print(f"🌐 EXTERNAL SOURCES: {metadata.get('external_sources', False)}")
            print(f"🏗️ CREATES TABLES: {metadata.get('creates_tables', False)}")
            
        else:
            procesados_con_error += 1
            print(f"❌ Error en análisis: {metadata['error']}")
        
        # Guardar progreso cada 5 SPs o al final
        if i % 5 == 0 or i == len(sps_a_procesar):
            if guardar_metadata_completa(metadata_existente):
                print(f"💾 Progreso guardado: {i}/{len(sps_a_procesar)}")
    
    # 5. Mostrar resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN FINAL")
    print(f"✅ SPs procesados exitosamente: {procesados_exitosos}")
    print(f"❌ SPs con error: {procesados_con_error}")
    print(f"📁 Total en metadata: {len(metadata_existente)}")
    
    # Guardar final
    guardar_metadata_completa(metadata_existente)

if __name__ == "__main__":
    procesar_sp_batch()