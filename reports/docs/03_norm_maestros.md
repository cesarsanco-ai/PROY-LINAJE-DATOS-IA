## 📄 Documentación Técnica: `src/02_processing/03_norm_maestros.py`

### 1. Descripción General
**¿Qué hace el script?**
Este script actúa como una capa de **Normalización**. Toma los nombres de objetos crudos (que pueden ser largos, contener caracteres especiales o ser inconsistentes) y genera un catálogo oficial con **IDs Únicos** (Primary Keys sintéticas).

Su objetivo es preparar los datos para sistemas más robustos, separando los metadatos ligeros del código SQL pesado.

### 2. Especificaciones de Ejecución

#### 📥 Input (Origen)
* **Carpeta:** `data_raw/`
* **Archivos:**
    * `dependencias_sql.csv` (Para listar relaciones).
    * `codigo_fuente.csv` (Para asociar el código SQL al maestro de procesos).

#### 📤 Output (Destino)
* **Carpeta:** `maestros/` (Nueva carpeta creada por el script).
* **Archivos Generados:**
    1.  `maestro_sp.json` (Catálogo completo de SPs con código).
    2.  `maestro_sp.csv` (Índice ligero de SPs).
    3.  `maestro_tablas.csv` (Catálogo de tablas).
    4.  `dependencias_normalizadas.csv` (Relaciones usando IDs).

---

### 3. Interpretación Detallada de Salidas

#### 📂 A. Maestros de Procesos (Stored Procedures)

**1. `maestro_sp.json` (La Fuente de Verdad)**
* **Formato:** JSON.
* **Por qué JSON:** El código SQL contiene saltos de línea, comillas y caracteres que suelen romper los formatos CSV. JSON maneja esto nativamente.
* **Contenido:** ID, Nombre y **Código SQL completo**.
* **Uso:** Cuando la IA necesite *leer* la lógica.

**2. `maestro_sp.csv` (El Índice Ligero)**
* **Formato:** CSV.
* **Contenido:** ID (`SP_00001`), Nombre y Longitud del código.
* **Uso:** Para mostrar listas rápidas en interfaces (UI) sin cargar megabytes de texto.

#### 📂 B. Maestro de Datos (Tablas)

**3. `maestro_tablas.csv`**
* **Contenido:** Asigna un ID único (`tb_00001`) a cada tabla detectada en el sistema.
* **Estructura:** `id_tabla`, `nombre_tabla`.

#### 📂 C. Tabla de Hechos (Relaciones)

**4. `dependencias_normalizadas.csv`**
* **Propósito:** Es la versión evolucionada de `dependencias_sql.csv`.
* **Cambio Clave:** En lugar de solo tener nombres, ahora incluye los IDs generados.
* **Estructura:** `id_sp` (Foreign Key), `id_tabla` (Foreign Key), `tipo_objeto`, `accion`.

---

### 4. Lógica de Identificación
El script aplica una generación de IDs secuenciales para garantizar unicidad y orden:
* **Stored Procedures:** Prefijo `SP_` + 5 dígitos (ej. `SP_00023`).
* **Tablas:** Prefijo `tb_` + 5 dígitos (ej. `tb_00105`).

---

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `4_6_generador_maestros.py` es el encargado de la **Normalización de Entidades**.
>
> Transforma los datos crudos de `data_raw` en un modelo relacional limpio en la carpeta `maestros/`.
> * Genera IDs únicos (`SP_XXXXX`, `tb_XXXXX`).
> * Separa el código SQL en un archivo JSON (`maestro_sp.json`) para evitar errores de formato en CSV.
> * Crea una tabla de enlaces (`dependencias_normalizadas.csv`) que usa estos IDs.
>
> **Importante:** Cualquier herramienta futura (dashboard o IA) debería leer de la carpeta `maestros/` en lugar de `data_raw` para asegurar integridad referencial."