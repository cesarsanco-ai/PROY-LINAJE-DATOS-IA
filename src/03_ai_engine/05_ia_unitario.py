
# antes:  4_8_extractor_ia_metadata_sp

# actual: src/03_ai_engine/05_ia_unitario.py
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

def buscar_sp_por_id(sp_id_buscado):
    """
    Busca un SP por ID en maestro_sp.json y retorna su código SQL
    """
    try:
        with open(FILE_MAESTRO_SP, 'r', encoding='utf-8') as f:
            maestro_sp = json.load(f)
        
        for sp in maestro_sp:
            if sp['id_sp'].lower() == sp_id_buscado.lower():
                return {
                    'id_sp': sp['id_sp'],
                    'nombre_sp': sp['nombre_sp'],
                    'codigo_sql': sp['codigo_sql']
                }
        
        return None  # No encontrado
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró {FILE_MAESTRO_SP}")
        return None
    except Exception as e:
        print(f"❌ Error buscando SP: {e}")
        return None

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
        print(f"📨 Respuesta IA recibida: {len(respuesta_texto)} caracteres")
        
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

def procesar_sp_automatico():
    """
    Función principal: pide ID de SP, busca en maestro_sp.json y extrae metadata
    """
    print("🔍 EXTRACTOR IA DE METADATA - AUTOMÁTICO (V7)")
    print("=" * 50)
    
    # 1. Pedir ID del SP
    sp_id = input("📝 Ingresa el ID del SP (ej: SP_00544): ").strip()
    
    if not sp_id:
        print("❌ Debes ingresar un ID de SP")
        return
    
    # 2. Buscar SP en maestro_sp.json
    print(f"\n🔎 Buscando SP: {sp_id}")
    sp_info = buscar_sp_por_id(sp_id)
    
    if not sp_info:
        print(f"❌ No se encontró el SP {sp_id}")
        return
    
    print(f"✅ SP encontrado: {sp_info['nombre_sp']}")
    print(f"📏 Longitud del código: {len(sp_info['codigo_sql'])} caracteres")
    
    # 3. Extraer metadata con IA
    print(f"\n🧠 Analizando código con IA...")
    metadata = extraer_metadata_sp(sp_info['codigo_sql'], sp_info['nombre_sp'])
    
    # 4. Mostrar resultados
    print(f"\n📊 RESULTADO DEL ANÁLISIS IA:")
    print("=" * 40)
    
    if "error" in metadata:
        print(f"❌ ERROR: {metadata['error']}")
        if "respuesta_cruda" in metadata:
            print(f"📄 Respuesta cruda: {metadata['respuesta_cruda'][:200]}...")
    else:
        print(f"🏷️  SP: {sp_info['nombre_sp']} ({sp_info['id_sp']})")
        print(f"📥 INPUTS ({len(metadata.get('inputs', []))}):")
        for input_tabla in metadata.get('inputs', []):
            print(f"   └─ {input_tabla}")
        
        print(f"📤 OUTPUTS ({len(metadata.get('outputs', []))}):")
        for output_tabla in metadata.get('outputs', []):
            print(f"   └─ {output_tabla}")
        
        print(f"🌐 EXTERNAL SOURCES: {metadata.get('external_sources', False)}")
        print(f"🏗️  CREATES TABLES: {metadata.get('creates_tables', False)}")
        
        # 5. Mostrar JSON completo
        print(f"\n📄 JSON COMPLETO:")
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        # 6. Ofrecer guardar en metadata
        guardar = input(f"\n💾 ¿Guardar esta metadata en banco_metadata_sp.json? (s/n): ").strip().lower()
        if guardar == 's':
            guardar_metadata_sp(sp_info['id_sp'], sp_info['nombre_sp'], metadata)

def guardar_metadata_sp(sp_id, nombre_sp, metadata):
    """
    Guarda la metadata en el banco_metadata_sp.json
    """
    try:
        # Cargar metadata existente o crear nuevo
        if os.path.exists(FILE_METADATA_SP):
            with open(FILE_METADATA_SP, 'r', encoding='utf-8') as f:
                metadata_completo = json.load(f)
        else:
            metadata_completo = []
            os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        
        # Buscar si ya existe este SP
        encontrado = False
        for sp in metadata_completo:
            if sp['id_sp'].lower() == sp_id.lower():
                sp.update({
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
            metadata_completo.append({
                "id_sp": sp_id.lower(),
                "nombre_sp": nombre_sp,
                "inputs": metadata.get("inputs", []),
                "outputs": metadata.get("outputs", []),
                "external_sources": metadata.get("external_sources", False),
                "creates_tables": metadata.get("creates_tables", False),
                "ai_review": True
            })
        
        # Guardar actualizado
        with open(FILE_METADATA_SP, 'w', encoding='utf-8') as f:
            json.dump(metadata_completo, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Metadata guardada en: {FILE_METADATA_SP}")
        
    except Exception as e:
        print(f"❌ Error guardando metadata: {e}")

if __name__ == "__main__":
    procesar_sp_automatico()