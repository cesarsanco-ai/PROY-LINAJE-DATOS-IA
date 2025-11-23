
## 📄 Documentación Técnica: `src/01_ingestion/02_grafo_base.py`

### 1\. Descripción General

**¿Qué hace el script?**
Este script ayuda a nuestro MVP funcionable y actúa como el "cerebro" del pipeline. Procesa la información cruda extraída en el paso anterior y construye un **Grafo Dirigido (Directed Graph)** utilizando la librería `networkx`.

Su función principal es transformar una lista simple de dependencias en un mapa de linaje con **direccionalidad**. Utiliza **Parsing de Código Estático** (con la librería `sqlglot`) para leer el código SQL y determinar si un Stored Procedure está **LEYENDO** (`SELECT`) o **ESCRIBIENDO** (`INSERT`/`UPDATE`) en una tabla.

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

  * **Fuente:** Carpeta `data_raw/` (generada por el script 1).
  * **Archivos Requeridos:**
      * `dependencias_sql.csv`: Relaciones base del sistema.
      * `codigo_fuente.csv`: Texto SQL para el análisis semántico.

#### 📤 Output (Destino)

  * **Ruta de Salida:** Carpeta `data_processed/` (creada automáticamente).
  * **Archivos Generados:**
    1.  `relaciones_finales.csv` (Tabular).
    2.  `linaje_completo.gexf` (Formato Gephi para visualización).
    3.  `linaje_completo.graphml` (Formato estándar de grafos para Python/NetworkX).

-----

### 3\. Lógica de Procesamiento (Parsing)

Para que la IA entienda cómo se derivan las relaciones, el script aplica esta heurística sobre el código SQL:

1.  **Carga Inicial:** Crea nodos y aristas base ("USA") desde las dependencias de SQL Server.
2.  **Análisis con SQLGlot:** Recorre el árbol sintáctico del código SQL.
      * **Detectar Escritura:** Si una tabla está dentro de un bloque `INSERT`, `UPDATE` o `CREATE` $\rightarrow$ La relación es **SP ESCRIBE EN TABLA** (Flujo: SP $\rightarrow$ Tabla).
      * **Detectar Lectura:** Si una tabla está dentro de un `SELECT` o `JOIN` $\rightarrow$ La relación es **TABLA LEÍDA POR SP** (Flujo: Tabla $\rightarrow$ SP).
      * **Tablas Temporales:** Si el nombre de la tabla contiene "XTMP", el nodo se etiqueta como `Temporal` (Color Naranja) para diferenciarlo de tablas maestras.

-----

### 4\. Interpretación Detallada de Salidas

#### 📂 Archivo 1: `relaciones_finales.csv`

  * **Propósito:** Listado plano de aristas con su dirección resuelta.
  * **Utilidad para la IA:** Es la fuente de verdad para entender el flujo de datos paso a paso.

**Ejemplo de Salida Esperada:**

```csv
Origen,Destino,Relacion
od_Venta_Diaria,RTM_OD_SP_CALCULAR_KPI,LEE
RTM_OD_SP_CALCULAR_KPI,XTMP_KPI_Resultado,ESCRIBE
XTMP_KPI_Resultado,RTM_OD_SP_EXPORTAR_BI,LEE
```

*(Nota: Aquí se ve claramente que el SP lee de una tabla diaria, escribe en una temporal, y luego otro SP lee esa temporal).*

#### 📂 Archivos de Grafo (`.gexf` / `.graphml`)

  * **Propósito:** Archivos binarios/XML que representan la topología de la red.
  * **Utilidad para la IA:** Permiten algoritmos de grafos complejos:
      * **Orden Topológico:** ¿En qué orden exacto debo ejecutar los scripts para no romper dependencias?
      * **Detección de Ciclos:** ¿Hay algún proceso que se llame a sí mismo y cause un bucle infinito?
      * **Análisis de Impacto:** Si cambio la tabla `A`, ¿qué reportes finales se rompen?

**Atributos de los Nodos:**

  * **Tipo:** `StoredProcedure` (Rojo), `Tabla` (Azul), `Temporal` (Naranja).

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `2_construir_grafo.py` procesa los datos crudos del paso 1. Utiliza la librería `networkx` para armar un grafo y `sqlglot` para analizar semánticamente el código SQL.
>
> **Su salida clave es `data_processed/relaciones_finales.csv` y los archivos de grafo (.gexf/.graphml).**
>
> A diferencia del paso 1, este script **resuelve la dirección del flujo**: determina explícitamente si un proceso **LEE** o **ESCRIBE** en una tabla, y clasifica las tablas intermedias (`XTMP`) como nodos temporales. Esto es vital para construir el orquestador de ejecución posterior. 

Nota Importante: Esto sirve para el MVP de prueba pero no para el proyecto real, ya que es muy limitada sqlgplot"