

## 📄 Documentación Técnica: `src/01_ingestion/01_ingesta_sql.py`

### 1\. Descripción General

**¿Qué hace el script?**
Automatiza la extracción de documentación técnica y linaje de datos desde una base de datos SQL Server. Se conecta específicamente para analizar la estructura, dependencias y código fuente de tablas (filtradas por los prefijos `od_` y `XTMP_`) y Procedimientos Almacenados.

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

  * **Fuente:** Servidor SQL Server (`10.20.20.88`).
  * **Base de Datos:** `Gloria_RTM`.
  * **Datos Requeridos:** Metadatos del sistema (`sys.tables`, `sys.columns`, `sys.sql_modules`, etc.).

#### 📤 Output (Destino)

  * **Ruta de Salida:** Carpeta local `data_raw/` (creada automáticamente en el directorio de ejecución).
  * **Archivos Generados:** 3 archivos CSV detallados a continuación.

-----

### 3\. Interpretación Detallada de Salidas

#### 📂 Archivo 1: `metadata_tablas.csv`

  * **Propósito:** Proporcionar el diccionario inicial de datos base que luego sera mejorado.
  * **Utilidad para la IA:** Permite conocer los tipos de datos en el MVP futuro para sugerir conversiones automáticas en Python/Pandas (ej. `nvarchar` $\rightarrow$ `string`, `decimal` $\rightarrow$ `float`) y entender la granularidad de la información.

**Ejemplo de Salida Esperada:**

```csv
Tabla,Columna,Tipo_Dato,Longitud,Es_Nulo
od_Venta_Diaria,Fecha_Venta,date,3,0
od_Venta_Diaria,Codigo_Cliente,varchar,20,0
od_Venta_Diaria,Monto_Total,decimal,17,1
XTMP_Clientes_Activos,ID_Cliente,int,4,0
XTMP_Clientes_Activos,Nombre,nvarchar,100,1
```

#### 📂 Archivo 2: `dependencias_sql.csv`

  * **Propósito:** Mapear el linaje de datos "oficial" detectado por las dependencias del motor SQL Server, servira como base para el MVP basico.
  * **Utilidad para la IA:** Ayuda a construir un grafo dirigido (DAG) para determinar el orden de procesamiento (qué tablas se deben cargar antes que otras).

**Ejemplo de Salida Esperada:**

```csv
Origen_SP,Destino_Tabla,Tipo_Objeto,Accion
RTM_OD_SP_CARGAR_VENTAS,od_Venta_Diaria,SQL_STORED_PROCEDURE,DEPENDENCY
RTM_OD_SP_CARGAR_VENTAS,XTMP_Control_Carga,SQL_STORED_PROCEDURE,DEPENDENCY
RTM_OD_SP_CALCULAR_KPI,od_Venta_Diaria,SQL_STORED_PROCEDURE,DEPENDENCY
```

#### 📂 Archivo 3: `codigo_fuente.csv`

  * **Propósito:** Contener la lógica de negocio cruda (el script SQL completo).
  * **Utilidad para la IA:** Es crucial para realizar "Parsing" (análisis de texto) y encontrar relaciones ocultas que el sistema no detecta automáticamente, como:
      * Uso de tablas temporales (`#Tabla`).
      * SQL Dinámico (`EXEC(...)`).
      * Lógica compleja de `INSERT`/`UPDATE`.

**Ejemplo de Salida Esperada:**

```csv
Nombre_Objeto,Tipo,Codigo_SQL
RTM_OD_SP_CARGAR_VENTAS,SQL_STORED_PROCEDURE,"CREATE PROCEDURE... INSERT INTO od_Venta_Diaria SELECT * FROM #TmpVentas..."
RTM_OD_SP_CALCULAR_KPI,SQL_STORED_PROCEDURE,"CREATE PROCEDURE... UPDATE T SET T.Valor = 100 FROM XTMP_Kpis T..."
```

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `1_extraccion_sqlserver.py` es un extractor de metadatos y código fuente que servira como base inicial para un MVP, asimismo mencionar que como es data origen necesita ser tratada para el proyecto real. Se conecta a SQL Server y descarga tres CSVs clave a la carpeta `data_raw`:
>
> 1.  **Estructura:** Definición de tablas y tipos de datos (`metadata_tablas.csv`).
> 2.  **Dependencias:** Relaciones reconocidas por el motor de base de datos (`dependencias_sql.csv`).
> 3.  **Lógica:** Código SQL completo de los Stored Procedures (`codigo_fuente.csv`) para análisis profundo de lógica de negocio."