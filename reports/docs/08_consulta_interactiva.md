
## 📄 Documentación Técnica: `src/04_lineage_core/08_consulta_interactiva.py`

### 1\. Descripción General

**¿Qué hace el script?**
Realiza un análisis de **Linaje de Datos Ascendente (Upstream Lineage)**.
Dado el nombre de una tabla objetivo (ej. `STG_VENTAS_CONSOLIDADA`), el script reconstruye recursivamente toda la cadena de procesos que contribuyeron a generar ese dato, nivel por nivel, hasta llegar a las fuentes originales.

**Diferencia Clave:**
A diferencia de los visualizadores simples (paso 3) que solo muestran vecinos directos, este script utiliza un algoritmo de búsqueda para profundizar hasta 10 niveles, cruzando información física (`dependencias_sql`) con información semántica (`metadata_sp` validada por IA).

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

Este script requiere que todo el ecosistema de datos esté sincronizado:

1.  **Estructura Física:** `data_raw/dependencias_sql.csv` (Quién escribe en la tabla).
2.  **Diccionarios:** `maestros/maestro_sp.csv` y `maestro_tablas.csv` (Para traducir Nombres $\leftrightarrow$ IDs).
3.  **Inteligencia Artificial:** `metadata/banco_metadata_sp.json` (Para saber qué inputs *reales* usa cada SP).

#### 📤 Output (Destino)

  * **Interfaz:** Consola (Texto plano / ASCII Art).
  * **Formato:** Árbol jerárquico de dependencias.
  * **Alertas:** Reporte de "Rutas Críticas" (puntos de riesgo).

-----

### 3\. Lógica Algorítmica (BFS - Breadth First Search)

El script implementa un algoritmo de **Búsqueda en Anchura** con una cola (`deque`):

1.  **Inicio:** Se encola la tabla objetivo como "Nivel 0".
2.  **Búsqueda de Generador:** Consulta `dependencias_sql.csv` para ver qué Stored Procedure tiene como `Destino_Tabla` la tabla actual.
3.  **Expansión Semántica:**
      * Localiza el SP encontrado en `banco_metadata_sp.json`.
      * Extrae sus `inputs` (Tablas que lee). **Nota:** Aquí es vital que la IA haya hecho su trabajo en los pasos 4.x, ya que SQL Server no siempre declara estos inputs explícitamente.
4.  **Recursividad:** Las tablas `inputs` encontradas se añaden a la cola para ser procesadas en el "Nivel + 1".
5.  **Condición de Parada:**
      * No hay SP que escriba en la tabla (Es una **Tabla Origen**).
      * Se alcanza la profundidad máxima (Default: 10).
      * Se detecta un ciclo (tabla ya visitada).

-----

### 4\. Interpretación de Salida

#### 🌳 Árbol de Trazabilidad

Muestra la historia del dato desde el final hasta el principio.

```text
📁 NIVEL 0 (El paso final):
----------------------------------------
   🔧 SP: RTM_OD_CARGAR_VENTAS (SP_00201)
      📤 Output: STG_VENTAS_CONSOLIDADA (Lo que pediste)
      📥 Inputs:
         └─ OD_VENTA_DIARIA (Se va al Nivel 1)
         └─ MAESTRO_CLIENTES (Se va al Nivel 1)

📁 NIVEL 1 (Los padres):
----------------------------------------
   🔧 SP: RTM_OD_ETL_LEGACY (SP_00055)
      📤 Output: OD_VENTA_DIARIA
      📥 Inputs:
         └─ RAW_VENTA_SAP (Se va al Nivel 2)

📁 NIVEL 2 (El origen):
----------------------------------------
   🏁 TABLA ORIGEN: RAW_VENTA_SAP
      🛣️ Camino: RAW_VENTA_SAP → SP:RTM_OD_ETL_LEGACY → OD_VENTA_DIARIA...
```

#### 🔍 Análisis de Rutas Críticas

Al final del reporte, el script destaca riesgos de auditoría:

  * **🌐 SPs con Fuentes Externas:** Procesos que usan `OPENROWSET`, `BULK INSERT` o Linked Servers. Son los puntos de entrada de datos al sistema.
  * **🏗️ SPs que Crean Tablas:** Procesos que hacen `CREATE TABLE`. Útil para detectar lógica volátil o temporal.

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `6_trazabilidad_tablas.py` es la herramienta de **investigación profunda**.
>
> **Uso:** Ejecútalo cuando necesites saber la procedencia exacta de una tabla específica.
> **Dependencia:** Es totalmente dependiente de la calidad de `metadata/banco_metadata_sp.json`. Si la IA no analizó los SPs en el paso 4, este árbol saldrá cortado o incompleto.
>
> **Funcionalidad:** Combina los hallazgos físicos del parser SQL con los hallazgos semánticos de la IA para dibujar el mapa completo de dependencias."