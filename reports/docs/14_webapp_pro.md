
## 📄 Documentación Técnica: `src/05_analytics_viz/14_webapp_pro.py` (Versión Avanzada/RAG-version 1)

### 1. Descripción General
**¿Qué hace el script?**
Es una aplicación web interactiva de **Auditoría Forense de Datos con IA**. A diferencia de la versión básica, esta herramienta implementa un sistema **RAG (Retrieval-Augmented Generation)**.

No solo muestra quién conecta con quién (grafo), sino que **lee el código fuente SQL** asociado a los objetos y se lo envía a GPT-4o-mini para que explique **qué lógica de negocio** se está aplicando, realice trazabilidad de linaje profunda y detecte transformaciones específicas.

### 2. Especificaciones de Ejecución

#### 📥 Input (Origen)
* **Grafo:** `data_processed/relaciones_finales.csv` (Estructura).
* **Código Fuente:** `data_raw/codigo_fuente.csv` (La "materia prima" para la IA).
* **Credenciales:** `api_key.txt`.

#### 📤 Output (Destino)
* **Interfaz Web:** Se ejecuta en local (Puerto 8501).
* **Funcionalidad:** Panel de control unificado con grafo estructural + análisis semántico de código.

---

### 3. Características Clave (Diferenciales)

#### 🧠 Motor RAG (Retrieval-Augmented Generation)
El script no "alucina" sobre lo que hace un SP; **lo lee**.
1.  El usuario selecciona un objeto (ej. `tb_Ventas_Final`).
2.  El script busca en el grafo qué Procedimientos Almacenados escriben en esa tabla.
3.  Recupera el código SQL real de esos SPs desde el diccionario en memoria.
4.  Construye un prompt gigante: *"Aquí tienes el código SQL real de los procesos que llenan esta tabla. Explícame la lógica..."*.

#### 🕵️‍♂️ Lógica de "Contexto Inverso"
Si seleccionas una **Tabla** (que no tiene código per se), el script es lo suficientemente inteligente para:
* Detectar que es un contenedor de datos.
* Buscar a sus "padres" (SPs que la alimentan).
* Extraer el código de los padres y enviarlo a la IA.
* **Resultado:** La IA te explica cómo se calcula un dato en la tabla final analizando el código del proceso previo.

#### 🔘 Modos de Análisis Pre-programados
Incluye "prompts de ingeniería" listos para usar:
* **🔍 Trazabilidad completa:** Pide a la IA reconstruir la cadena de dependencias en formato ASCII.
* **📊 Lógica de Negocio:** Pide un resumen funcional para humanos.
* **⚙️ Análisis Técnico:** Pide detalles de `JOINs`, filtros `WHERE` y agregaciones.

---

### 4. Interpretación de la Interfaz

* **Panel Izquierdo (Hechos):** Muestra la verdad matemática del grafo (Nodos padres/hijos). Incluye un desplegable `📜 Ver Código SQL Crudo` para validación manual.
* **Panel Derecho (Interpretación):** Es el cerebro de la IA.
    * Si seleccionas "Trazabilidad", intentará generar un árbol jerárquico de texto.
    * Muestra qué SPs específicos se están analizando para dar la respuesta.

---

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `4_5_app_streamlit.py` es la herramienta principal de análisis. **Debe ser la elección por defecto para consultas complejas.**
>
> **Capacidades Únicas:**
> 1.  **Carga el Código Fuente:** Tiene acceso a la lógica interna de los SPs.
> 2.  **Inyección de Contexto:** Cuando analizas una tabla, inyecta el código de los SPs que la alimentan para explicar el origen del dato.
> 3.  **Ingeniería de Prompts:** Tiene instrucciones específicas para generar árboles de linaje y explicaciones de negocio basadas en evidencia (código real).
>
> Usa este script para responder preguntas como: *'¿Cómo se calcula la columna Venta_Neta?'* o *'¿Cuál es la ruta completa desde el origen hasta esta tabla?'*."