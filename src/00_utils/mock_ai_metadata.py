
import json
import os
import sys

# Add src to path to import config_paths
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from config_paths import PROCESSED_DIR, KNOWLEDGE_DIR, ensure_directories

def mock_ai_processing():
    ensure_directories()
    print("🤖 MOCK AI PROCESSOR - Simulando análisis de Inteligencia Artificial...")
    
    file_maestro = os.path.join(PROCESSED_DIR, "maestro_sp.json")
    file_metadata = os.path.join(KNOWLEDGE_DIR, "banco_metadata_sp.json")
    
    if not os.path.exists(file_maestro):
        print("❌ No existe maestro_sp.json. Ejecuta Fase 2 primero.")
        return

    with open(file_maestro, 'r') as f:
        maestro_sp = json.load(f)
        
    metadata_list = []
    
    print(f"📋 Procesando {len(maestro_sp)} SPs...")
    
    for sp in maestro_sp:
        nombre_sp = sp['nombre_sp']
        codigo = sp['codigo_sql'].upper()
        
        # Heurística simple para simular IA
        inputs = []
        outputs = []
        
        # Detectar outputs (INSERT INTO table)
        if "od_clientes" in nombre_sp or "INSERT INTO OD_CLIENTES" in codigo:
            outputs.append("od_clientes")
        if "od_ventas" in nombre_sp or "INSERT INTO OD_VENTAS" in codigo:
            outputs.append("od_ventas")
            # Update también cuenta como output/modificación
            if "UPDATE OD_CLIENTES" in codigo:
                if "od_clientes" not in outputs: outputs.append("od_clientes")
                
        # Detectar inputs (FROM table)
        if "stage_crm_clientes" in codigo or "FROM STAGE_CRM_CLIENTES" in codigo:
            inputs.append("stage_crm_clientes")
        if "stage_pos_sales" in codigo or "FROM STAGE_POS_SALES" in codigo:
            inputs.append("stage_pos_sales")
            
        metadata_entry = {
            "id_sp": sp['id_sp'],
            "nombre_sp": nombre_sp,
            "inputs": inputs,
            "outputs": outputs,
            "external_sources": False,
            "creates_tables": False,
            "ai_review": True
        }
        
        metadata_list.append(metadata_entry)
        print(f"   ✅ Analizado: {nombre_sp} -> IN: {inputs} | OUT: {outputs}")

    with open(file_metadata, 'w') as f:
        json.dump(metadata_list, f, indent=2)
        
    print(f"✨ Metadata simulada guardada en {file_metadata}")
    print("🚀 Ahora puedes ejecutar la Fase 4 (Lineage Core)")

if __name__ == "__main__":
    mock_ai_processing()
