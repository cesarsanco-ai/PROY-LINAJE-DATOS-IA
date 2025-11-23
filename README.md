# 🕵️‍♂️ Sistema de Linaje de Datos & Auditoría con IA (RTM Gloria)

Este proyecto implementa un pipeline de Ingeniería de Datos para extraer, procesar y analizar el linaje de datos de SQL Server. Utiliza Grafos (NetworkX) e Inteligencia Artificial (OpenAI) para entender la lógica de negocio oculta en los Stored Procedures.

---

## 🚀 Guía de Ejecución (Pipeline)

El sistema debe ejecutarse en orden secuencial. Sigue estos pasos para actualizar todo el conocimiento del sistema.

### 🔴 FASE 1: Ingesta y Estructura (Requiere VPN)
*Estos scripts conectan a la base de datos real. Si fallan, revisa tu VPN.*

1.  **`python src/01_ingestion/01_ingesta_sql.py`**
    * 📝 **Qué hace:** Descarga el catálogo de tablas y el código fuente crudo de SQL Server.
    * 📂 **Salida:** Actualiza `data/01_raw/`.

2.  **`python src/01_ingestion/02_grafo_base.py`**
    * 📝 **Qué hace:** Construye el primer grafo de dependencias usando *parsing* estático (sin IA).
    * 📂 **Salida:** Genera `data/02_processed/linaje_completo.gexf`.

### 🟠 FASE 2: Normalización (Procesamiento Local)
*Estos scripts son rápidos y no requieren internet.*

3.  **`python src/02_processing/03_norm_maestros.py`**
    * 📝 **Qué hace:** Crea catálogos únicos de SPs y Tablas con IDs estandarizados.
    * 📂 **Salida:** Genera `data/02_processed/maestro_*.csv`.

4.  **`python src/02_processing/04_init_metadata.py`**
    * 📝 **Qué hace:** Prepara el esqueleto JSON para que la IA lo rellene luego.
    * ⚠️ **Nota:** Reinicia la metadata. Solo ejecutar si quieres empezar de cero.

### 🟡 FASE 3: Motor de Inteligencia Artificial (⚠️ COSTO $$)
*Estos scripts consumen créditos de la API de OpenAI. Úsalos con precaución.*

5.  **`python src/03_ai_engine/05_ia_unitario.py`**
    * 🧪 **Modo Test:** Procesa UN solo Stored Procedure por ID. Úsalo para probar si el prompt funciona.

6.  **`python src/03_ai_engine/06_ia_masivo.py`**
    * 🏭 **Modo Producción:** Barre todos los SPs pendientes.
    * 💰 **Impacto:** Lee el código SQL y detecta inputs/outputs reales.
    * ✅ **Inteligente:** Solo procesa lo que falta (`ai_review: false`).

### 🟢 FASE 4: Compilación del Linaje (Core)
*Cruza la estructura física (Fase 1) con la inteligencia semántica (Fase 3).*

7.  **`python src/04_lineage_core/07_compilador_master.py`**
    * 🧠 **EL CEREBRO:** Construye el árbol de trazabilidad completo (Deep Lineage) y lo guarda en disco.
    * 📂 **Salida:** Genera `data/04_gold/maestro_trazabilidad_completo.json`.

---

## 📊 Visualización y Consumo

Una vez ejecutado el pipeline, puedes usar estas herramientas en cualquier orden:

* **Reporte Global:**
    `python src/05_analytics_viz/10_reporte_global.py`
    Genera estadísticas de salud del sistema en `data/04_gold/`.

* **Análisis Visual (EDA):**
    `python src/05_analytics_viz/11_eda_salud.py`
    Genera gráficos de complejidad y riesgos en `reports/eda/01_salud_sistema/`.

* **WebApp Interactiva (Streamlit):**
    `streamlit run src/05_analytics_viz/14_webapp_pro.py`
    Levanta la interfaz web para consultar el linaje y chatear con la IA sobre el código.

---

## ⚙️ Configuración Inicial

1.  **Entorno Virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # o venv\Scripts\activate en Windows
    pip install -r requirements.txt
    ```

2.  **Variables de Entorno:**
    Crea un archivo `config/.env` basado en `config/.env.example` con tus credenciales:
    ```env
    SQL_SERVER=10.10.10.10
    SQL_DATABASE=BBDD_propia
    ...
    ```

3.  **API Key:**
    Asegúrate de tener tu clave en `config/api_key.txt`.