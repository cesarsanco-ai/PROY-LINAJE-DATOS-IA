## 📄 Documentación Técnica: `src/02_processing/04_init_metadata.py`

### 1\. Descripción General

**¿Qué hace el script?**
Genera un repositorio inicial de metadatos (`banco_metadata_sp.json`) para todos los Stored Procedures catalogados.

**⚠️ Nota Importante:** En esta versión específica, el script **SIMULA** la lógica de inputs y outputs.
No está leyendo el código SQL real para determinar estas relaciones (eso lo hacen los scripts 2 y 4.5). Su objetivo aquí es **crear la estructura de datos JSON** necesaria para que el sistema funcione, rellenando campos con datos algorítmicos (dummy data) y banderas básicas basadas en el nombre, listo para ser sobrescrito posteriormente por un análisis real de IA.

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

  * **Carpeta:** `maestros/` (Generada en el paso 4.6).
  * **Archivos:**
      * `maestro_sp.csv`: Lista de procedimientos a procesar.
      * `maestro_tablas.csv`: Lista de tablas disponibles para asignar como inputs/outputs simulados.

#### 📤 Output (Destino)

  * **Carpeta:** `metadata/` (Nueva carpeta creada por el script).
  * **Archivos Generados:**
    1.  `banco_metadata_sp.json` (Archivo principal para consumo de aplicaciones).
    2.  `banco_metadata_sp.csv` (Versión tabular para revisión humana).

-----

### 3\. Estructura del Objeto Metadata

El script estandariza el formato JSON que describirá a cada Stored Procedure en el futuro.

**Ejemplo de un objeto generado:**

```json
{
  "id_sp": "SP_00023",
  "nombre_sp": "RTM_OD_CARGAR_VENTAS",
  "inputs": ["tb_00012", "tb_00005"],  <-- (Asignado por algoritmo en este paso)
  "outputs": ["tb_00040"],             <-- (Asignado por algoritmo en este paso)
  "external_sources": true,            <-- (Detectado por palabra clave 'cargar')
  "creates_tables": false,
  "ai_review": false                   <-- (Flag clave: Indica que la IA aún no validó esto)
}
```

### 4\. Lógica de Simulación (Placeholder)

Para que la IA futura no se confunda, es vital entender cómo se llenan estos datos actualmente:

1.  **Inputs/Outputs:** Se asignan usando lógica matemática (`sp_index % 3`) sobre la lista de tablas maestras. **No son relaciones reales.**
2.  **Flags (`external_sources`, `creates_tables`):** Se infieren buscando palabras clave simples en el nombre del SP (ej. "importar", "generar", "crear").
3.  **Estado Inicial:** El campo `ai_review` se inicializa en `False`.

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `4_7_generador_metadata_sp.py` crea la estructura base de metadatos en la carpeta `metadata/`.
>
> **ADVERTENCIA CRÍTICA:** Los datos de linaje (`inputs`/`outputs`) dentro de `banco_metadata_sp.json` generados por este script son **SIMULADOS (Mock Data)**.
>
> Este script sirve para inicializar el archivo JSON con el formato correcto, pero **no contiene la verdad del negocio** sobre las relaciones. Su propósito es preparar el terreno para que un proceso posterior (o la IA) actualice este JSON con datos reales y cambie el flag `ai_review` a `True`."