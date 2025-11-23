

## 📄 Documentación Técnica: `src/03_ai_engine/05_ia_unitario.py`

### 1\. Descripción General

**¿Qué hace el script?**
Es una herramienta interactiva de **Extracción de Metadatos asistida por IA**.
Permite al usuario ingresar el ID de un Stored Procedure (ej. `SP_00544`), recuperar su código fuente real desde el archivo maestro, y enviarlo a GPT-4o-mini para que identifique **semánticamente**:

1.  Tablas de Entrada (`FROM`, `JOIN`).
2.  Tablas de Salida (`INSERT`, `UPDATE`).
3.  Fuentes Externas (`BULK INSERT`, `OPENROWSET`).
4.  Creación de objetos volátiles (`CREATE TABLE #Tmp`).

Su función crítica es **validar y sobrescribir** la metadata simulada, cambiando el estado del registro a "Revisado por IA".

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

  * **Archivo Maestro:** `maestros/maestro_sp.json` (De aquí lee el código SQL real).
  * **Credenciales:** `api_key.txt`.
  * **Interacción de Usuario:** Requiere ingresar el `ID_SP` por consola.

#### 📤 Output (Destino)

  * **Consola:** Muestra el JSON resultante del análisis.
  * **Persistencia:** Actualiza el archivo `metadata/banco_metadata_sp.json`.

-----

### 3\. Lógica de Procesamiento (El Cerebro)

#### A. Recuperación (Retrieval)

Busca en el JSON maestro el bloque de código SQL correspondiente al ID ingresado.

#### B. Análisis Cognitivo (Prompt Engineering)

Envía el código a la API de OpenAI con instrucciones estrictas:

  * **Restricción de Formato:** "Responde SOLO con un JSON válido".
  * **Definición de Roles:** Inputs = Lectura, Outputs = Escritura.
  * **Límite de Contexto:** Recorta el código a 12,000 caracteres para optimizar costos y tokens.

#### C. Actualización de Estado (Flagging)

Cuando el usuario confirma guardar, el script actualiza el registro en `banco_metadata_sp.json` y realiza un cambio fundamental:

  * **Antes:** `ai_review: false` (Datos simulados).
  * **Después:** `ai_review: true` (Datos validados por IA).

-----

### 4\. Interpretación de Salida

**Ejemplo de JSON extraído por la IA:**

```json
{
    "inputs": ["od_Venta_Diaria", "Maestro_Clientes"],
    "outputs": ["stg_Venta_Consolidada"],
    "external_sources": false,
    "creates_tables": true
}
```

**Diferencia vs Paso 4.7:**

  * En el paso 4.7, los inputs se elegían matemáticamente (`id % 3`).
  * En este paso 4.8, los inputs son **reales**, extraídos de leer el código `SELECT * FROM od_Venta_Diaria...`.

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `4_8_extractor_ia_metadata_sp.py` es la herramienta de **validación unitaria**.
>
> Se usa para **procesar un SP específico** y obtener su linaje real mediante IA.
>
>   * Lee el código fuente real de `maestros/maestro_sp.json`.
>   * Utiliza GPT-4o-mini para analizar el SQL.
>   * Actualiza `metadata/banco_metadata_sp.json` poniendo el flag **`ai_review: true`**.
>
> **Importancia:** Es el único script (junto con el 4.5) que genera linaje basado en contenido semántico real, corrigiendo las simulaciones estructurales de los pasos anteriores."