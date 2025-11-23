
## 📄 Documentación Técnica: `src/04_lineage_core/09_qa_profundidad.py`

### 1\. Descripción General

**¿Qué hace el script?**
Es un **Motor de Trazabilidad Profunda (Deep Lineage Engine)**.
A diferencia de los scripts de visualización (que muestran vecinos directos), este algoritmo utiliza **BFS (Breadth-First Search)** para recorrer el grafo de dependencias "hacia atrás" (upstream) nivel por nivel.

Combina dos mundos:

1.  **La Estructura Física:** Las dependencias crudas de SQL (`dependencias_sql.csv`).
2.  **La Capa Semántica:** La metadata validada por IA (`banco_metadata_sp.json`).

Su objetivo es responder la pregunta definitiva: *"Si miro la tabla X, ¿cuál es su origen primigenio, pasando por todos los procedimientos intermedios?"*

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

Requiere la sincronización de todas las capas de datos anteriores:

  * **Estructura:** `data_raw/dependencias_sql.csv`.
  * **Identidad:** `maestros/maestro_sp.csv` y `maestro_tablas.csv`.
  * **Inteligencia:** `metadata/banco_metadata_sp.json` (Es vital que este archivo tenga datos reales generados por el script 4.8 o 4.9).

#### 📤 Output (Destino)

  * **Interfaz de Consola:** Genera un reporte jerárquico en texto (ASCII Tree).
  * **Análisis de Riesgo:** Identifica "Rutas Críticas" (SPs que leen de fuentes externas o crean estructuras volátiles).

-----

### 3\. Lógica Algorítmica (BFS)

El script no solo "dibuja" el grafo, lo **navega**:

1.  **Punto de Partida:** El usuario ingresa una tabla (ej. `DM_Ventas`).
2.  **Explosión de Nivel 1:** Busca qué SPs escriben en `DM_Ventas`.
3.  **Consulta de Metadata:** Para cada SP encontrado, consulta el JSON de metadata para ver sus **Inputs Reales** (validados por IA).
4.  **Recursividad (Cola):** Esos inputs se añaden a una cola de procesamiento para analizar *sus* padres en el siguiente ciclo.
5.  **Condición de Parada:** El algoritmo se detiene cuando llega a una "Tabla Origen" (nadie escribe en ella, solo se lee) o alcanza la profundidad máxima (10 niveles).

-----

### 4\. Interpretación de Salida

**Ejemplo de Reporte en Consola:**

```text
🎯 RESUMEN DEL ÁRBOL DE TRAZABILIDAD
==================================================
📊 Tabla raíz: STG_VENTAS_CONSOLIDADA
📈 Profundidad máxima: 3
📦 Tablas origen: 2

📁 NIVEL 0:
----------------------------------------
   🔧 SP: RTM_OD_CARGAR_VENTAS (SP_00201)
      📤 Output: STG_VENTAS_CONSOLIDADA
      📥 Inputs:
         └─ OD_VENTA_DIARIA (Nivel 1)
         └─ MAESTRO_CLIENTES (Nivel 1)

📁 NIVEL 1:
----------------------------------------
   🔧 SP: RTM_OD_ETL_LEGACY (SP_00055)
      📤 Output: OD_VENTA_DIARIA
      📥 Inputs:
         └─ RAW_VENTA_SAP (Nivel 2)

📁 NIVEL 2 (Origen):
----------------------------------------
   🏁 TABLA ORIGEN: RAW_VENTA_SAP
      🛣️ Camino: RAW_VENTA_SAP → SP:RTM_OD_ETL_LEGACY → OD_VENTA_DIARIA...
```

### 5\. Análisis de Rutas Críticas

El script destaca automáticamente nodos peligrosos o importantes:

  * 🌐 **Fuentes Externas:** Si un SP en la cadena hace un `OPENROWSET` (detectado por la IA en el paso 4), este script lo marca como un punto de entrada de datos al sistema.
  * 🏗️ **Creación de Tablas:** Si un SP altera el esquema (`CREATE TABLE`), se notifica para auditoría.

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `5_8_test_dependencias.py` (o `6_trazabilidad_completa.py`) es el **orquestador final de linaje**.
>
> **Función:** Realiza ingeniería inversa del flujo de datos completo.
> **Dependencia Crítica:** Funciona gracias a que los scripts `4.x` limpiaron y estructuraron la metadata. Si la metadata está vacía o simulada, este script mostrará un árbol incompleto.
>
> Úsalo para generar reportes de auditoría textual y validar la profundidad real de las dependencias de una tabla crítica."