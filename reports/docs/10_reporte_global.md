## 📄 Documentación Técnica: `src/05_analytics_viz/10_reporte_global.py`

### 1\. Descripción General

**¿Qué hace el script?**
Es un **Generador de Reportes de Gobernanza**.
Analiza la totalidad de los metadatos y dependencias para generar estadísticas globales. Clasifica automáticamente todos los activos del sistema (Tablas y SPs) y detecta "Puntos Calientes" (Hotspots) de complejidad.

**Propósito:** Responder preguntas de alto nivel como:

  * *"¿Cuántas tablas origen tenemos?"*
  * *"¿Cuáles son las 10 tablas más críticas del sistema?"*
  * *"¿Qué procesos dependen de fuentes externas?"*

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

Requiere la carga completa de la base de conocimiento:

  * **Inteligencia:** `metadata/banco_metadata_sp.json` (Validado por IA).
  * **Identidad:** `maestros/maestro_tablas.csv` y `maestro_sp.csv`.

#### 📤 Output (Destino)

  * **Carpeta:** `resultados/` (Creada automáticamente).
  * **Archivos Generados:**
    1.  `maestro_trazabilidad_completo.json`: Un "Mega-JSON" que contiene todo el grafo de dependencias y estadísticas para ser consumido por dashboards (Power BI, Streamlit).
    2.  `output_trazabilidad.txt`: Un reporte ejecutivo en texto plano, legible por humanos.

-----

### 3\. Lógica de Clasificación

El script aplica reglas de negocio para etiquetar los objetos:

#### 🏭 Clasificación de Stored Procedures

  * **SP Generador:** Aquel que tiene al menos una tabla en su lista de `outputs` (Escribe datos).
  * **SP Usuario:** Aquel que solo tiene `inputs` (Solo lee datos, ej. reportes finales).

#### 🗃️ Clasificación de Tablas

  * **Tabla Generada:** Existe al menos un SP que escribe en ella. (Es una tabla intermedia o final).
  * **Tabla Origen:** Ningún SP del sistema escribe en ella. (Se asume que es una tabla Raw/Source que viene de sistemas externos).

-----

### 4\. Interpretación de Salida (`output_trazabilidad.txt`)

El reporte de texto destaca tres secciones críticas para la toma de decisiones:

#### A. Estadísticas Globales

Resumen ejecutivo del volumen del sistema.

```text
📊 ESTADÍSTICAS GLOBALES:
----------------------------------------
Total tablas en el sistema: 450
Tablas origen: 120 (Datos que vienen de fuera)
Tablas con generadores: 330 (Datos calculados internamente)
```

#### B. Top 10 Tablas Complejas

Identifica los cuellos de botella. La "complejidad" se mide por cuántos SPs escriben en ella o la leen.

```text
🏆 TOP 10 TABLAS MÁS COMPLEJAS:
----------------------------------------
1. STG_VENTAS_CONSOLIDADA (tb_00102)
    SPs generadores: 5 (¡Alto riesgo de concurrencia!)
    SPs usuarios: 42 (Muy usada aguas abajo)
```

#### C. SPs Críticos (Riesgo Externo)

Lista los procedimientos que la IA detectó con `external_sources: true`.

```text
⚠️ SPs MÁS CRÍTICOS (con fuentes externas):
----------------------------------------
1. RTM_OD_IMPORTAR_SAP (SP_00001)
    Tablas generadas: ['RAW_VENTAS']
```

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `6_3_reporte_global_sistema.py` es una herramienta de **Gobernanza y Documentación Masiva**.
>
> **Diferencia vs Script 6:**
>
>   * El Script 6 es interactivo (pregunta por *una* tabla).
>   * El Script 6.3 es automático (procesa *todo* y genera archivos estáticos).
>
> **Uso:** Ejecutar este script periódicamente para actualizar la documentación oficial del sistema en la carpeta `resultados/`. Es ideal para entregar reportes de estado a gerencia o arquitectura de datos."