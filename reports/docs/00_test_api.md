## 📄 Documentación Técnica: `src/00_utils/00_test_api.py`

### 1\. Descripción General

**¿Qué hace el script?**
Es un script de **diagnóstico y validación de infraestructura**. Su única función es verificar que las credenciales de OpenAI sean válidas y que el entorno de ejecución tenga conexión a internet para alcanzar la API. Actúa como un "Sanity Check" (prueba de cordura) antes de ejecutar procesos más costosos o complejos.

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

  * **Archivo Requerido:** `api_key.txt` (Debe estar en la misma carpeta que el script).
  * **Contenido:** Únicamente la clave de API (string raw, p.ej. `sk-...`).
  * **Lógica de Lectura:** El script incluye un paso de limpieza (`.strip()`) para eliminar espacios en blanco o saltos de línea accidentales que suelen corromper la autenticación.

#### 📤 Output (Destino)

  * **Destino:** Consola / Terminal (Stdout).
  * **Archivos Generados:** Ninguno. (Este script no persiste datos en disco).

-----

### 3\. Interpretación Detallada de Salidas

#### 🖥️ Salida en Consola

**Propósito:** Confirmación visual inmediata.

**Escenario A: Éxito (Salida Esperada)**
La IA responde una frase corta y divertida confirmando operatividad.

```text
📂 Leyendo archivo api_key.txt...
   ✅ Key encontrada (Longitud: 51 caracteres)
🔌 Conectando con OpenAI...
🚀 Enviando mensaje a GPT-4o-mini...

========================================
🤖 RESPUESTA DE LA IA:
¡Estoy vivito, coleando y listo para la acción! 🚀
========================================

✅ ¡CONEXIÓN EXITOSA! Tu API Key funciona perfectamente.
```

**Escenario B: Fallo (Manejo de Errores)**
El script captura excepciones críticas para evitar que el usuario pierda tiempo debugueando scripts más complejos.

  * *Error de Archivo:* "❌ ERROR: No encuentro el archivo 'api\_key.txt'"
  * *Error de Autenticación:* "Incorrect API key provided..."
  * *Error de Saldo:* "You exceeded your current quota..."

-----

### 4\. Lógica del Modelo

  * **Modelo Utilizado:** `gpt-4o-mini` (Seleccionado por ser rápido y de bajo costo para pruebas).
  * **Prompt de Sistema:** "Responde solo con una frase corta y divertida." (Para minimizar consumo de tokens y facilitar la lectura humana).

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `3_5_test_api_simple.py` es una herramienta de diagnóstico aislada. **No procesa datos de negocio.**
>
> Su función es estrictamente **validar la conectividad con OpenAI**.
>
> 1.  Lee la credencial desde `api_key.txt`.
> 2.  Realiza una petición mínima a `gpt-4o-mini`.
> 3.  Imprime el resultado en consola.
>
> **Regla de uso:** Si este script falla, **NO** se debe proceder con la ejecución de los scripts de generación de documentación o análisis (pasos siguientes), ya que todos fallarán por error de autenticación."