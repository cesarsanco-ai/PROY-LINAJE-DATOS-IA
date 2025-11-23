## 📄 Documentación Técnica: `src/05_analytics_viz/11_eda_salud.py`

### 1\. Descripción General

**¿Qué hace el script?**
Ejecuta un **Análisis Exploratorio de Datos (EDA)** sobre el maestro de trazabilidad generado en el paso anterior.
Utiliza librerías de ciencia de datos (`pandas`, `matplotlib`, `seaborn`) y grafos (`networkx`) para convertir el archivo JSON estático en **Insights Visuales**.

**Propósito:** Transformar los datos técnicos de linaje en un "Chequeo de Salud" (Health Check) del ecosistema de datos, respondiendo preguntas como:

  * *"¿Cuál es la tabla más crítica de todo el sistema?"* (Centralidad).
  * *"¿Tenemos Stored Procedures demasiado complejos (God Objects)?"*
  * *"¿Qué dominios funcionales (Ventas, Clientes) dominan el almacén de datos?"*

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

  * **Fuente:** `resultados/maestro_trazabilidad_completo.json` (Generado por el script 6.3/7).
  * **Requisitos:** Librerías gráficas instaladas (`pip install matplotlib seaborn networkx`).

#### 📤 Output (Destino)

  * **Carpeta:** `eda_maestro_trazabilidad/` (Creada automáticamente).
  * **Archivos Generados:**
    1.  **Gráficos PNG:** 4 paneles visuales de alta resolución.
    2.  **Grafo Exportable:** `grafo_dependencias.gexf` (Para abrir en Gephi).
    3.  **Reporte de Texto:** `reporte_insights.txt` (Resumen ejecutivo).

-----

### 3\. Módulos de Análisis

#### 📊 A. Análisis General (`01_analisis_general.png`)

  * **Distribución:** ¿Qué porcentaje son tablas origen vs. tablas calculadas?
  * **Top Uso:** Identifica las tablas más leídas (tablas maestras muy solicitadas).
  * **Top Generación:** Identifica tablas donde escriben muchos SPs distintos (posible riesgo de concurrencia o mala arquitectura).

#### 🔍 B. Complejidad de Procesos (`02_complejidad_sps.png`)

  * **Scatter Plot Inputs vs Outputs:** Visualiza la "huella" de cada SP.
      * *Puntos altos en ambos ejes:* SPs monolíticos complejos.
      * *Puntos bajos:* SPs atómicos/simples.
  * **Clasificación:** Muestra cuántos SPs realizan acciones destructivas/creativas (`CREATE TABLE`).

#### 🕸️ C. Teoría de Redes (`03_analisis_red.png` y `.gexf`)

  * **Construcción del Grafo:** Crea un grafo dirigido donde Nodos = Tablas/SPs y Aristas = Flujo de datos.
  * **Algoritmos de Centralidad:** Calcula qué nodos son los "hubs" de la red. Si uno de estos nodos falla, el impacto sistémico es masivo.
  * **Exportación GEXF:** Genera un archivo que permite visualizar la red en 3D o con algoritmos de fuerza en herramientas externas como Gephi.

#### 🎯 D. Patrones Semánticos (`04_patrones_tablas.png`)

  * **Análisis de Prefijos:** Detecta estándares de nomenclatura (ej. uso de `od_`, `dim_`, `stg_`).
  * **Dominios Funcionales:** Busca palabras clave en los nombres (`VENTA`, `CLIENTE`, `LOGISTICA`) para entender qué áreas de negocio consumen más recursos de datos.

-----

### 4\. Interpretación de Salida (`reporte_insights.txt`)

El script redacta automáticamente un diagnóstico basado en los datos:

```text
REPORTE DE INSIGHTS - SISTEMA DE TRAZABILIDAD
================================================================================
INSIGHTS GENERALES:
• Total de tablas: 450
• Tablas origen: 120

TABLAS CRITICAS (Alto impacto):
  1. MAESTRO_CLIENTES -> 85 SPs usuarios (Si esta tabla se rompe, 85 procesos fallan).

RIESGOS IDENTIFICADOS:
• Puntos unicos de fallo:
  - STG_VENTAS_GLOBAL (demasiadas dependencias)
• SPs demasiado complejos:
  - RTM_OD_CALCULO_MASIVO (25 inputs -> Candidato a refactorización).

RECOMENDACIONES:
1. Considerar refactorizacion de tablas sobreutilizadas...
```

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `8_eda_trazabilidad.py` es el **Generador de Dashboards Estáticos**.
>
> **Uso:** Ejecútalo después de generar el maestro de trazabilidad para obtener visualizaciones y estadísticas de gobernanza.
> **Valor Único:**
>
> 1.  **Detecta Anomalías:** Encuentra SPs anormalmente grandes o tablas anormalmente usadas.
> 2.  **Exportación GEXF:** Permite llevar el grafo a herramientas profesionales de visualización de redes.
> 3.  **Semántica:** Entiende de qué trata el negocio analizando los nombres de las tablas (Ventas vs. Logística)."

===========



### RESULTADOS DE IMAGENES###

Este análisis es **fundamental** para entender a qué "bestia" nos estamos enfrentando. Los gráficos revelan una arquitectura de datos con **alta dependencia de tablas temporales y lógicas centralizadas en pocos objetos maestros**.

Aquí tienes el **Diagnóstico Técnico y de Complejidad** basado en las imágenes generadas por `8_eda_trazabilidad.py`. 

---

## 📊 Diagnóstico de Salud del Ecosistema de Datos (Resultados EDA)

### 1. Arquitectura: "Heavy Staging" y Dependencia de Temporales
* **Evidencia:** En el gráfico *Distribución de Tipos de Tablas* (Img 04), vemos una cantidad masiva de tablas con prefijo `XTMP` (>500), superando incluso a las tablas operativas `od`.
* **Diagnóstico:** El sistema utiliza una estrategia de **ETL basada en Staging Físico**. En lugar de realizar transformaciones en memoria o vistas, los procesos escriben constantemente en tablas intermedias (`XTMP`).
* **Impacto en Consultas:**
    * **Complejidad Alta:** Para rastrear un dato final, la IA tendrá que saltar por muchas tablas `XTMP` que son volátiles.
    * **Riesgo:** Si intentamos consultar una tabla `XTMP` fuera del horario de ejecución del ETL, podría estar vacía. **Las consultas deben apuntar a las tablas `od_` o finales, no a las `XTMP`.**

### 2. Puntos Críticos (Cuellos de Botella)
* **Evidencia:** En *Top 10 Tablas Más Utilizadas* (Img 01), la tabla `od_minorista_tb_parametros` es consumida por más de **110 SPs distintos**. Le siguen `ciudades` y `cartera_vigente`.
* **Diagnóstico:** Estas son las **Tablas Maestras del Sistema**. Son el corazón. Cualquier cambio en la estructura de `tb_parametros` rompería más de 100 procesos simultáneamente.
* **Impacto en Consultas:** Estas tablas son los **nodos seguros** para hacer `JOIN`. Son las dimensiones confiables del sistema.

### 3. Riesgo de Concurrencia y "Spaghetti Code"
* **Evidencia:** En *Top 10 Tablas Más Generadas* (Img 01, abajo-izq), la tabla `od_minorista_tb_programacion_d...` es escrita por **14 Stored Procedures diferentes**.
* **Diagnóstico (Bandera Roja 🚩):** Esto es un anti-patrón arquitectónico. Tener múltiples "autores" para una misma tabla sugiere que la lógica de negocio está fragmentada. Es difícil saber cuál de los 14 SPs es el responsable de un dato erróneo en un momento dado.
* **Impacto en Consultas:** Si preguntamos "¿Cómo se calcula la programación?", la respuesta no es única. La IA deberá preguntar por el contexto (¿Programación de qué canal? ¿De qué tipo de venta?) para elegir el SP correcto de los 14 posibles.

### 4. Complejidad Cognitiva de los Procedimientos (God Objects)
* **Evidencia:** En *Top 10 SPs Más Complejos* (Img 02), vemos procedimientos como `RTM_OD_MINORISTA_SP_VENTA...` que toman **14 tablas de entrada (Inputs)** para generar sus salidas.
* **Diagnóstico:** Tenemos **"God Objects"** (Objetos Dios). Son SPs monolíticos que hacen demasiadas cosas a la vez. Probablemente contienen miles de líneas de código con lógica de negocio dura.
* **Impacto en Consultas:** Explicar la lógica de estos SPs será difícil. La IA necesitará hacer un análisis profundo (Deep Lineage) porque la transformación no es directa; cruza 14 fuentes de datos distintas.

### 5. Dominio Funcional
* **Evidencia:** En *Distribución por Dominios* (Img 04), los dominios `VENTA` y `CLIENTE` dominan absolutamente el sistema.
* **Diagnóstico:** Es un sistema puramente transaccional/comercial (RTM - Route to Market).
* **Impacto:** El vocabulario del negocio girará en torno a "Pedidos", "Liquidaciones" y "Coberturas".

---

### 🚀 Conclusión para la Estrategia de IA

Dado este diagnóstico visual, la complejidad de las consultas que haremos se clasifica como **ALTA**.

1.  **Navegación:** La IA debe ser capaz de distinguir entre tablas efímeras (`XTMP`) y tablas persistentes (`od`).
2.  **Trazabilidad:** No basta con ver el SP inmediato. Debido a los "God Objects", la IA debe ser capaz de explicar lógica que combina más de 10 fuentes de datos.
3.  **Interdependencia:** El sistema es altamente acoplado (Red densa en Img 03). Tocar una tabla maestra impacta en todo el grafo.

**Acción Inmediata:**
Mantener los scripts `6_trazabilidad_tablas.py` (Deep Lineage) y `7_constructor...` es **obligatorio**. Sin ellos, sería imposible para un humano o una IA entender de dónde sale un dato en un entorno con más de 500 tablas temporales y SPs con 14 inputs.