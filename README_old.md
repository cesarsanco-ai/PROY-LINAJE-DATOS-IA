# **PROMPT PARA IA - CONTEXTO COMPLETO DEL PROYECTO**

---

## **🎯 CONTEXTO GENERAL**
**Proyecto:** Sistema de Trazabilidad y Linaje de Datos para Base de Datos SQL Server  
**Objetivo:** Reverse engineering completo de 730 tablas y 545 stored procedures para mapear dependencias, impactos y flujos de datos

---

## **🏗️ ARQUITECTURA DESARROLLADA**

### **1. EXTRACCIÓN (Scripts 1-7)**
```python
# Pipeline completo de minería de metadatos
1_extractor_metadatos.py      → Catálogo de tablas/SPs
2_analizador_dependencias.py  → Dependencias SQL parsing
3_maestro_trazabilidad.py     → Consolidación central
4_visualizador_red.py         → Grafos interactivos
5_buscador_impactos.py        → Consultas de impacto
6_exportador_documentacion.py → Documentación automática
7_monitor_cambios.py          → Detección de cambios
```

### **2. ANÁLISIS EDA (Script 8)**
```python
8_eda_trazabilidad.py → Análisis exploratorio visual
```
**Salidas:** 4 dashboards + reporte insights + grafo GEXF

### **3. TRAZABILIDAD AUTOMÁTICA (Script 9 - EN DESARROLLO)**
```python
9_trazabilidad_automatica.py → Motor de consultas inteligentes
```

---

## **💪 FORTALEZAS LOGRADAS**

### **✅ METADATOS COMPLETOS**
- **730 tablas** catalogadas (427 con generadores, 303 origen)
- **545 stored procedures** analizados (421 generadores, 124 usuarios)
- **100% de dependencias** mapeadas con precisión

### **✅ ARQUITECTURA ROBUSTA**
- **Grafo dirigido** con 1,275+ nodos y 2,500+ relaciones
- **Sistema de caching** para performance
- **Múltiples perspectivas**: impacto, dependencia, flujos

### **✅ VISUALIZACIÓN AVANZADA**
- **4 dashboards EDA** con matplotlib/plotly
- **Grafo interactivo** exportable a Gephi
- **Heatmaps, redes, distribuciones**

### **✅ DOCUMENTACIÓN AUTOMÁTICA**
- **Reportes PDF/HTML** generados automáticamente
- **Diccionario de datos** completo
- **Documentación técnica** y de negocio

---

## **🚨 DEBILIDADES CRÍTICAS - URGENTE**

### **❌ PROBLEMA PRINCIPAL: JSON MASIVO INMANEJABLE**
```json
{
  "tablas": {
    "XTMP_od_minorista_tb_clientes_fileupload_10_llamadas": {
      // 730 objetos como este...
    }
  }
}
```
**Impacto:** 
- Script 9 se traba al procesar 2.5MB de JSON
- Consultas de trazabilidad timeout
- Análisis en memoria colapsa

### **❌ ARQUITECTURA MONOLÍTICA**
- **Un solo JSON gigante** → cuello de botella
- **Sin base de datos** → todo en memoria RAM
- **Sin paginación** → carga completa siempre

### **❌ PERFORMANCE CRÍTICA**
- **Trazabilidad profunda**: 5+ niveles = minutos
- **Búsquedas complejas**: O(n) lineal inaceptable
- **Grafo muy denso**: Algoritmos O(n²) imposibles

### **❌ USABILIDAD CERO**
- **Interfaz inexistente** → solo código
- **Sin API REST** → imposible integrar
- **Sin cache distribuido** → recalcula todo

---

## **📊 EVIDENCIAS TÉCNICAS**

### **DATOS EDA RECIENTES:**
```
🔴 TABLAS CRÍTICAS IDENTIFICADAS:
1. od_minorista_tb_ciudades → 76 SPs dependen (punto único fallo)
2. od_minorista_tb_ventas_preventa_pedidos → 33 SPs 
3. od_minorista_tb_parametros → 112 SPs (¡CRÍTICO!)

🔴 SPs MÁS COMPLEJOS:
• RTM_OD_MINORISTA_SP_VENTA_NETA_CLIENTES_PRODUCTOS_CANASTAS_CARGAR → 10 inputs
• RTM_OD_MINORISTA_SP_LIQUIDADO_TEMPORALES_VENTA_CARGAR → 13 inputs
```

### **PATRONES DE RIESGO:**
- **12 tablas** con >20 dependencias (puntos únicos de fallo)
- **8 SPs** con >8 inputs (demasiado complejos)
- **45% tablas temporales** (arquitectura frágil)

---

## **🎯 OBJETIVO INMEDIATO: SCRIPT 9**

### **FUNCIONALIDADES PLANEADAS:**
```python
class TrazabilidadAutomatica:
    def buscar_impacto(tabla):          # ¿Qué se afecta si cambio X?
    def buscar_origen(tabla):           # ¿De dónde viene esta data?
    def buscar_dependencias(sp):        # ¿Qué necesita este SP?
    def visualizar_flujo(origen, destino)  # ¿Cómo fluyen los datos?
    def generar_reporte_impacto()       # Reporte ejecutivo
```

### **PROBLEMAS ANTICIPADOS:**
1. **JSON de 2.5MB** no cabe en algoritmos recursivos
2. **Grafo con 2,500+ aristas** colapsa búsquedas
3. **Sin indexación** → búsquedas O(n) imposibles

---

## **🆘 SOLICITUD DE AYUDA CRÍTICA**

### **NECESITO:**
**Arquitectura escalable** para reemplazar el JSON monstruoso, que permita:
1. **Consultas rápidas** de trazabilidad (< 3 segundos)
2. **Búsquedas complejas** con múltiples criterios  
3. **Interfaz usable** (Web/API/CLI)
4. **Manejo eficiente** del grafo masivo

### **TENGO DISPONIBLE:**
- JSON completo con toda la metadata
- Scripts 1-8 funcionando perfectamente
- Análisis EDA con insights críticos
- Tiempo para implementar nueva arquitectura

---

## **💡 POSIBLES SOLUCIONES A EVALUAR**

¿Base de datos graph? (Neo4j)  
¿SQLite con tablas relacionales?  
¿Elasticsearch para búsquedas?  
¿API FastAPI con cache Redis?  
¿Dividir JSON en chunks?

**¿Cuál recomiendas implementar URGENTE para salvar el proyecto?**

---





============= REVISADO




### 📋 PROMPT DE CONTEXTO: PROYECTO "AUDITOR de linaje de datos con GRAPH-RAG de tablas de una BBDD"

**ROL:** Eres un Arquitecto de Datos Senior y Especialista en MLOps. Tu objetivo es guiarme en la evolución de mi proyecto de Maestría en IA y Data.

**1. CONTEXTO DEL NEGOCIO**
Estoy desarrollando un sistema de **Auditoría de Linaje de Datos SQL Server** para una empresa retail de consumo masivo de alimentos y bebiddas("Gloria S.A.").
* **El Problema:** La lógica de negocio vive en cientos de Stored Procedures (SPs) complejos en SQL Server, algunos anidados. Rastrear de dónde sale una tabla de datos (fisica o temporal) (ej. "Venta Bruta") es una tarea forense manual lenta porque hay cadenas profundas de dependencia y tablas temporales (`XTMP`) indetectables por herramientas estándar de librerias de python.
* **El Objetivo:** Crear una herramienta que permita preguntar en lenguaje natural: *"¿Cómo se calcula la tabla X?"* y obtener la trazabilidad exacta y la explicación lógica.
 '''
 Ejemplo base de salida:
 "Tu tabla "mi_tablida_xyz" con codigo tb_000wp esta en la capa 0, para la capa 1 tiene dependencias de 8 SPs de los cuales 2 SPs son generadores de tablas, y el resto 6 SPs son SPs que no generan la tabla que buscas, ya que su output de esos SPs no coincide con tu tabla de busqueda, por tanto solo se muestra los sps generadores y asi sucesivamente en cada rastreo de tablas, ya que cada tabla tiene en un maestro sps asociados, que algunos son sps generadores y otros sps pasivos que no influyen.
Se adjunta resumen, donde para ver su equivalencia, busque en su diccionario de datos los nombres a los que corresponde "
 
tb_001 → sp_010 → tb_005 → sp_022 → tb_020
tb_001 → sp_010 → tb_005 → sp_022 → tb_021
tb_001 → sp_010 → tb_006
tb_001 → sp_011 → tb_007 → sp_030 → tb_040 → sp_044 → tb_090
tb_001 → sp_014 → tb_008 → sp_015 → tb_009

Interpretacion: la tabla que buscas tb_001 esta en la capa 0, tiene 5 ramas completas con SP generadores validos. Las tablas origen que llevan a tb_001 son las tablas tb 20,21,6,90,9 que se encuentran en distintas capas, pero la capa mas profunda es la capa 4, por la tabla tb_090 usando sp: 11,30,44. Estas tablas son las q alimentan tu tabla por SP generadores que se muestran arriba, los cuales son validos, es decir toman la tabla de origen y la llevan y contribuyen en tu tb_001.
'''
**2. ARQUITECTURA TÉCNICA (MVP ACTUAL)**
Ya tengo un MVP funcional corriendo en local con este flujo, pero necesito detectar los errores, antes de pasarlo a un llm, estepuede verse muy complicado por eso, debe tener la logica ya calculada de la trazabilidad con codigo, hice pruebas con trababilidad erronea, pero funcionable a nivel UI:

* **A. Ingesta (`1_extraccion_sqlserver.py`):**
    * Script Python (`pyodbc`) que conecta a SQL Server.
    * Extrae metadatos y, lo más importante, el **Código Fuente SQL** (`sys.sql_modules`) y las **Dependencias Oficiales** (`sys.sql_expression_dependencies`) a archivos CSV locales (`data_raw/`).
* **B. Procesamiento (`2_construir_grafo.py`):**
    * Usa la librería **`sqlglot`** para parsear el código SQL extraído.
    * Construye un Grafo Dirigido con **`NetworkX`** (Nodos: Tablas/SPs, Aristas: Origen/Destino).
    * *Logro clave:* Detecta relaciones "invisibles" (tablas temporales `XTMP`) leyendo los `INSERT` y `FROM` dentro del código.
    * Genera un CSV de relaciones procesadas (`relaciones_finales.csv`).
* **C. Frontend (`4_5_app_streamlit.py`):**
    * Aplicación web en **Streamlit**.
    * **Panel Izquierdo:** Muestra la trazabilidad estructural (Padres e Hijos del nodo seleccionado) usando el grafo `NetworkX`.
    * **Panel Derecho:** Chat con IA (**OpenAI GPT-4o-mini**).
    * **Lógica RAG:** Cuando el usuario selecciona una Tabla (que no tiene código), el sistema busca a sus "Padres" (los SPs que escriben en ella), extrae su código SQL y se lo inyecta al Prompt del LLM para que explique la lógica de transformación.

**3. LIMITACIONES ACTUALES (LO QUE DEBO SOLUCIONAR AHORA)**
* **Grafo Incompleto:** El parser estático (`sqlglot`) falla con sintaxis compleja de T-SQL, por eso se uso aqui la api de openai para extraer la metadata de esos sp, dandome principalmente quienes eran tablas input y quienes tabla output".
* **Costos/Eficiencia:** El LLM re-analiza el código cada vez que pregunto, gastando tokens repetidamente.
* **Detección de Fuentes Externas:** No distinguimos si una tabla viene de un Excel (`BULK INSERT`) o es nativa.
* **Profundidad:** La trazabilidad visual es solo de Nivel 1 (Padres directos), necesito ver la cadena completa hasta la fuente raíz.

**4. PLAN DE TRABAJO (LO QUE ESPERO DE TI)**
Necesito evolucionar este MVP hacia una arquitectura **"Bitmask + Semantic Index"** para hacerlo profesional y escalable (MLOps).

Ayúdame a implementar la siguiente estrategia en mis archivos de código existentes:
1.  **Sistema de Bitmask:** Asignar un código binario a cada nodo (ej. 1=Fuente, 2=SP, 4=Reporte) para saber "qué es" sin preguntar a la IA.
2.  **Índice Semántico (Caché):** Crear un JSON local que guarde las explicaciones de la IA. Antes de llamar a la API, consultar este caché.
3.  **Detección Heurística:** Modificar la ingesta para detectar patrones de carga externa (`OPENROWSET`, `.csv`) y marcarlos en el grafo.
4.  **Trazabilidad Profunda:** Usar algoritmos de grafos para mostrar la ruta completa del dato (Ancestros/Descendientes) y no solo el vecino inmediato.

**INSTRUCCIÓN:**
Analiza los archivos de código que te proporcionaré a continuación (`1_extraccion...`, `2_construir...`, `4_5_app...`) y dime exactamente qué bloques de código debo modificar o agregar para implementar el **Punto 1 (Bitmask)** y el **Punto 3 (Detección Heurística)** primero. Sé técnico y dame el código en Python listo para integrar.

***