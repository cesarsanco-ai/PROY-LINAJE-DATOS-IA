# src/00_utils/00_test_api.py
import os
import sys
from openai import OpenAI

# ==============================================
# 1. CONFIGURACIÓN DE RUTAS (NUEVO)
# ==============================================
# Obtenemos la ruta de este script (src/00_utils/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para llegar a 'src/'
src_dir = os.path.dirname(current_dir)
# Agregamos 'src' al path para importar config_paths
sys.path.append(src_dir)

# Importamos la ruta de la API KEY
from config_paths import API_KEY_FILE

# ==============================================
# 2. LEER LA API KEY
# ==============================================
print(f"📂 Leyendo archivo desde: {API_KEY_FILE}...")

try:
    # USAMOS LA VARIABLE IMPORTADA EN LUGAR DEL NOMBRE A MANO
    with open(API_KEY_FILE, "r") as f:
        # .strip() borra espacios en blanco al inicio o final
        mi_api_key = f.read().strip()
    print(f"   ✅ Key encontrada (Longitud: {len(mi_api_key)} caracteres)")
except FileNotFoundError:
    print(f"   ❌ ERROR: No encuentro el archivo en: {API_KEY_FILE}")
    exit()

# ==============================================
# 3. CONFIGURAR CLIENTE Y TEST
# ==============================================
print("🔌 Conectando con OpenAI...")
try:
    client = OpenAI(api_key=mi_api_key)
except Exception as e:
    print(f"   ❌ Error al configurar cliente: {e}")
    exit()

print("🚀 Enviando mensaje a GPT-4o-mini...")

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Responde solo con una frase corta y divertida."},
            {"role": "user", "content": "Confirma que estás vivo y listo para trabajar."}
        ],
        max_tokens=50
    )
    
    respuesta = response.choices[0].message.content
    print("\n" + "="*40)
    print(f"🤖 RESPUESTA DE LA IA:\n{respuesta}")
    print("="*40 + "\n")
    print("✅ ¡CONEXIÓN EXITOSA! Tu API Key funciona perfectamente.")

except Exception as e:
    print("\n❌ LA CONEXIÓN FALLÓ.")
    print(f"Error detallado: {e}")
    print("Revisa que tu API Key sea correcta y tengas saldo/créditos.")