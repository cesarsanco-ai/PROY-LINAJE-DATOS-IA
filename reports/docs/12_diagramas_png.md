

## 📄 Documentación Técnica: `src/05_analytics_viz/12_diagramas_png.py`

### 1. Descripción General
**¿Qué hace el script?**
Este script es la capa de **presentación visual** del pipeline. Convierte las relaciones abstractas y tabulares generadas en el paso anterior en **Diagramas de Linaje** gráficos (imágenes PNG).

Su objetivo es permitir una auditoría visual rápida de procesos específicos ("Unit Testing Visual"), aislando un Stored Procedure y mostrando únicamente sus inputs (tablas que lee) y outputs (tablas que escribe).

### 2. Especificaciones de Ejecución

#### 📥 Input (Origen)
* **Fuente:** Archivo `data_processed/relaciones_finales.csv` (Output del script 2).
* **Datos:** Lista de aristas (Origen $\rightarrow$ Destino) con el tipo de relación (`LEE`, `ESCRIBE`, `USA`).

#### 📤 Output (Destino)
* **Ruta de Salida:** Carpeta `output_images/` (creada automáticamente).
* **Archivos Generados:** Imágenes `.png` individuales por cada Stored Procedure analizado.

---

### 3. Lógica de Visualización (Leyenda)
El script utiliza la librería `networkx` para la topología y `matplotlib` para el renderizado. Aplica una lógica de colores semántica para facilitar la lectura del flujo de datos:

#### 🎨 Código de Colores (Nodos y Aristas)
* **Nodos (Objetos):**
    * 🟡 **Oro (`gold`):** El Stored Procedure central que se está analizando (Foco de atención).
    * 🟢 **Verde Claro (`lightgreen`):** Tablas relacionadas (ya sean origen o destino).

* **Aristas (Flechas/Flujos):**
    * 🔴 **Flecha ROJA (`ESCRIBE`):** Indica impacto/modificación. El SP inserta o actualiza datos en la tabla. (Flujo: SP $\rightarrow$ Tabla).
    * 🔵 **Flecha AZUL (`LEE`):** Indica consumo. El SP lee datos de la tabla para cálculos. (Flujo: Tabla $\rightarrow$ SP).
    * ⚪ **Flecha GRIS (`USA`):** Dependencia genérica detectada por SQL Server sin dirección clara (fallback).

#### 📐 Lógica de Subgrafos
Para evitar generar un gráfico gigante e ilegible (conocido como "hairball"), el script **no dibuja toda la base de datos**.
1.  Selecciona un SP de la lista `sps_a_graficar`.
2.  Filtra el grafo global para obtener **solo** ese nodo y sus vecinos inmediatos (Tablas input/output).
3.  Aplica un algoritmo de distribución (`spring_layout`) para separar visualmente los elementos.

---

### 4. Interpretación de Salida

#### 🖼️ Archivo: `linaje_[NOMBRE_SP].png`
**Propósito:** Documentación visual para validación con el negocio o auditoría técnica.

**Ejemplo de Interpretación Visual:**
* Si ves una tabla con **flecha azul** entrando al nodo amarillo (SP) y una **flecha roja** saliendo del nodo amarillo hacia otra tabla, visualmente confirmas un proceso ETL clásico: **Extracción (Azul) $\rightarrow$ Transformación (Amarillo) $\rightarrow$ Carga (Roja)**.

---

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `3_visualizador_lineaje.py` genera diagramas estáticos de flujo de datos.
>
> Utiliza el CSV de relaciones del paso 2 y crea imágenes PNG en `output_images/`.
> **Convención Visual Clave:**
> * **Rojo (Arista):** Escritura/Output (Peligroso/Modificación).
> * **Azul (Arista):** Lectura/Input (Fuente).
> * **Amarillo (Nodo):** El Proceso (Stored Procedure).
>
> Este script es útil para validar visualmente si la lógica de `LEE`/`ESCRIBE` detectada por el parser SQL es correcta antes de documentar."

Nota importante: no impacta mucho en el proyecto real, solo era para validar si funcionaba la real y se concluyó que no, ya que la libreria sqlgplot es limitada y no ayudo al proposito real, pero si ayudo para el MVP para que muestra data al momemot de probar la interafaz con streamlit, es decir solo ayudo para maquetacion hasta este paso.