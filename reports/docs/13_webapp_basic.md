

## 📄 Documentación Técnica: `src/05_analytics_viz/13_webapp_basic.py` (Versión Básica de prueba)

### 1. Descripción General
**¿Qué hace el script?**
Es una aplicación web interactiva construida con **Streamlit**. Su función es servir como "Explorador de Relaciones". Permite al usuario seleccionar una Tabla o Procedimiento Almacenado y ver inmediatamente quién lo alimenta (Inputs) y a quién alimenta (Outputs).

**Diferencia Clave:** Esta versión incluye un chat con IA, pero es **genérico**. La IA actúa como un experto en SQL "ciego": sabe definiciones técnicas generales, pero **NO lee ni conoce el código fuente** de tu proyecto.

### 2. Especificaciones de Ejecución

#### 📥 Input (Origen)
* **Fuente de Datos:** `data_processed/relaciones_finales.csv` (Carga el grafo de relaciones).
* **Credenciales:** `api_key.txt` (Para habilitar el chat con GPT-4o-mini).
* **Código Fuente:** ❌ **NO LO CARGA**. (Esta es la principal limitación).

#### 📤 Output (Destino)
* **Interfaz Web:** Se ejecuta en el navegador (localmente, puerto 8501).
* **Visualización:** Listas de dependencias y tablas de datos filtradas.

---

### 3. Funcionalidad Principal

#### 🕸️ Explorador de Grafos (Panel Izquierdo)
Utiliza la librería `networkx` para buscar vecinos inmediatos del objeto seleccionado:
* **Predecesores (Inputs):** Muestra flechas entrando (`⬅️`).
* **Sucesores (Outputs):** Muestra flechas saliendo (`➡️`).
* **Utilidad:** Respuesta rápida a la pregunta "¿Qué tablas toca este SP?" sin abrir el código.

#### 🤖 Chat Genérico (Panel Derecho)
Conecta con OpenAI (`gpt-4o-mini`) con una configuración de bajo coste.
* **Prompt del Sistema:** *"Eres un asistente experto en SQL y Datos..."*
* **Limitación:** Como no se le inyecta el código SQL del proyecto, si le preguntas *"¿Qué lógica aplica el SP_CALCULAR_VENTAS?"*, la IA inventará una respuesta plausible (alucinación) o te dará una definición teórica, porque **no tiene el contexto real**.

---

### 4. Comparativa Técnica (vs versión 4.5)

| Característica | Versión 4.0 (Esta) | Versión 4.5 (La Avanzada) |
| :--- | :--- | :--- |
| **Carga de Código** | ❌ No lee SQL. | ✅ Lee `codigo_fuente.csv`. |
| **Inteligencia** | 🧠 **Genérica** (Sabe SQL teórico). | 🧠 **Contextual** (Conoce TU código). |
| **Velocidad** | ⚡ Muy rápida (carga ligera). | 🐢 Un poco más lenta (carga pesada). |
| **Uso Ideal** | Auditoría rápida de relaciones. | Análisis profundo de lógica de negocio. |

---

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `4_app_streamlit.py` es la **interfaz de visualización ligera**.
>
> 1. Carga el CSV de relaciones (`relaciones_finales.csv`) en un grafo simple.
> 2. Permite navegar entre nodos (Tablas/SPs) para ver dependencias directas.
> 3. Incluye un chat con GPT-4o-mini, pero **sin contexto RAG**.
>
> **Nota de Uso:** Este script es útil para demostraciones rápidas de conectividad o revisión estructural simple donde no se requiere que la IA explique la lógica de negocio específica."