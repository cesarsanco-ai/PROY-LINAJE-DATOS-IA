

## 📄 Documentación Técnica: `src/03_ai_engine/06_ia_masivo.py`

### 1\. Descripción General

**¿Qué hace el script?**
Es el **Procesador por Lotes (Batch Processor)** del sistema.
Automatiza la extracción de metadatos mediante IA para **todos** los Stored Procedures pendientes.
Su lógica principal es **incremental**: compara el maestro de SPs contra la metadata existente y solo procesa aquellos que **no** tienen el flag `ai_review: true`.

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

  * **Maestro:** `maestros/maestro_sp.json` (Fuente del código).
  * **Metadata Actual:** `metadata/banco_metadata_sp.json` (Base de datos de estado).
  * **Credenciales:** `api_key.txt`.

#### 📤 Output (Destino)

  * **Persistencia:** Actualiza (sobrescribe) el archivo `metadata/banco_metadata_sp.json` con la nueva información validada.
  * **Seguridad:** Realiza un "guardado parcial" cada 5 procesamientos para evitar pérdida de datos si el script se detiene.

-----

### 3\. Lógica de Flujo de Trabajo

#### A. Detección de "Delta" (Pendientes)

El script no reprocesa lo que ya está listo.

1.  Carga la metadata existente.
2.  Identifica qué IDs ya tienen `ai_review: true`.
3.  Filtra el maestro y crea una lista de **`sps_no_analizados`**.

#### B. Modos de Ejecución

Para controlar el consumo de la API (costos), ofrece dos modos:

  * **Modo X (Prueba/Demo):** Procesa solo los primeros **5** SPs pendientes. Útil para verificar que el prompt funciona antes de gastar créditos.
  * **Modo Z (Producción):** Procesa **TODOS** los SPs pendientes en un bucle continuo.

#### C. Extracción y Guardado

Utiliza la misma lógica de prompt que el script 4.8 (Inputs/Outputs/Fuentes Externas).

  * **Resiliencia:** Si un SP falla (error de API o JSON malformado), el script lo registra como error pero **continúa** con el siguiente. No detiene el lote completo.

-----

### 4\. Interpretación de Salida

**Consola (Log de Ejecución):**

```text
🔍 SPs no analizados: 45
📝 Selecciona modo (X/Z): Z

==================================================
📋 SP 1/45: RTM_OD_CARGAR_CLIENTES (SP_00102)
🔄 Enviando a IA...
✅ Analizado exitosamente
   📥 INPUTS: 2
   📤 OUTPUTS: 1
💾 Progreso guardado: 5/45
...
```

**Resultado en JSON (`banco_metadata_sp.json`):**
El archivo pasa de tener datos simulados (del paso 4.7) a datos reales semánticos.

```json
{
  "id_sp": "SP_00102",
  "nombre_sp": "RTM_OD_CARGAR_CLIENTES",
  "inputs": ["Maestro_Clientes", "Log_Ventas"],  <-- Real (detectado por IA)
  "outputs": ["Dim_Cliente"],                    <-- Real (detectado por IA)
  "external_sources": false,
  "creates_tables": false,
  "ai_review": true                              <-- Flag que evita reprocesamiento
}
```

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `4_9_barrido_masivo_metadata.py` es el motor de carga masiva.
>
> **Características Clave:**
>
> 1.  **Idempotente:** Solo procesa lo que falta (donde `ai_review` es false). Puedes ejecutarlo múltiples veces sin duplicar trabajo ni costos.
> 2.  **Batch Saving:** Guarda el progreso cada 5 registros.
> 3.  **Consumo de API:** Este script es el que mayor consumo de tokens genera, ya que envía el código completo de todos los SPs a OpenAI.
>
> **Uso:** Ejecutar este script después de `4_7` para poblar la base de conocimientos con datos reales antes de usar las herramientas de visualización finales."