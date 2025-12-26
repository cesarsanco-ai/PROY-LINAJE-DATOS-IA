# Arquitectura del Sistema de Linaje de Datos & Auditoría con IA

Este documento detalla la arquitectura técnica de la solución, mostrando cómo interactúan los componentes para transformar metadatos crudos en conocimiento de negocio mediante IA.

## 🏗️ Esquema de Arquitectura Lógica

El sistema sigue una arquitectura de **Pipeline Local** dividida en 5 capas secuenciales.

```mermaid
graph TD
    %% Estilos de los nodos
    classDef sql fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef python fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef storage fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef viz fill:#fff8e1,stroke:#fbc02d,stroke-width:2px;

    %% Nodos
    SQL[("🛢️ SQL Server<br/>(Origen)")]:::sql
    
    subgraph "Capa 1: Ingesta (src/01)"
        INGEST[("📥 Ingesta SQL<br/>(pyodbc)")]:::python
        RAW[("📂 Data Lake Raw<br/>(CSV)")]:::storage
    end

    subgraph "Capa 2: Procesamiento (src/02)"
        NORM[("⚙️ Normalizador<br/>(Pandas)")]:::python
        PARSER[("🕸️ Parser Estático<br/>(NetworkX)")]:::python
        PROC[("📂 Data Processed<br/>(GEXF, CSV)")]:::storage
    end

    subgraph "Capa 3: Motor de IA (src/03)"
        IA_ENG[("🧠 AI Engine<br/>(OpenAI GPT-4o)")]:::ai
        KNOW[("📂 Knowledge Base<br/>(JSON Enriquecido)")]:::storage
    end

    subgraph "Capa 4: Core de Linaje (src/04)"
        COMPILER[("🔗 Compilador Master<br/>(Deep Lineage)")]:::python
        GOLD[("📂 Data Gold<br/>(Trazabilidad Completa)")]:::storage
    end

    subgraph "Capa 5: Consumo (src/05)"
        APP[("🖥️ WebApp Pro<br/>(Streamlit)")]:::viz
        REP[("📊 Reportes<br/>(Matplotlib/Seaborn)")]:::viz
    end

    %% Relaciones
    SQL -->|Metadata + Código| INGEST
    INGEST --> RAW
    RAW --> NORM
    RAW --> PARSER
    NORM --> PROC
    PARSER --> PROC
    PROC --> IA_ENG
    IA_ENG -->|Análisis Semántico| KNOW
    PROC --> COMPILER
    KNOW --> COMPILER
    COMPILER --> GOLD
    GOLD --> APP
    GOLD --> REP
    RAW -->|Consulta Código| APP
```

## 🧩 Descripción de Componentes

### 1. Ingesta y Extracción (`src/01_ingestion`)
*   **Responsabilidad:** Extraer la "verdad física" del servidor de base de datos.
*   **Interacciones:** Conecta vía ODBC al SQL Server. Descarga:
    *   *System Catalog:* Tablas, columnas y tipos de datos.
    *   *Dependencies:* Relaciones de llave foránea declaradas.
    *   *Source Code:* Definiciones T-SQL puras de Stored Procedures.

### 2. Normalización y Parsing (`src/02_processing`)
*   **Responsabilidad:** Limpiar y estructurar la data cruda.
*   **Interacciones:**
    *   Genera identificadores únicos universales (UIDs) para cada objeto (ej. `SP_001`, `TB_023`) para evitar ambigüedades por nombres repetidos.
    *   Construye el **Grafo Base** usando análisis estático. Este grafo conecta objetos basándose en referencias explícitas en el código, pero ignora la lógica dinámica.

### 3. Motor de Inteligencia Artificial (`src/03_ai_engine`)
*   **Responsabilidad:** Comprender la semántica y lógica oculta.
*   **Interacciones:**
    *   Consume el código fuente de los SPs desde la capa Processed.
    *   Envía *chunks* de código a **OpenAI (GPT-4o)** con un prompt especializado en ingeniería inversa de SQL.
    *   Extrae:
        *   **Inputs/Outputs Reales:** Tablas que realmente se leen/escriben (más allá de lo declarado).
        *   **Lógica de Negocio:** Reglas de transformación explicadas en lenguaje natural.
        *   **Dependencias Ocultas:** Tablas temporales y saltos lógicos no evidentes.

### 4. Compilador de Linaje (Deep Lineage Core) (`src/04_lineage_core`)
*   **Responsabilidad:** Unificar el grafo físico con el conocimiento semántico.
*   **Interacciones:**
    *   Fusiona el grafo de NetworkX con los JSONs de metadata de la IA.
    *   Resuelve la recursividad del linaje (Padre -> Hijo -> Nieto) para construir el árbol de trazabilidad completo.
    *   Detecta rutas críticas y puntos de ruptura.

### 5. Visualización Interactiva (`src/05_analytics_viz`)
*   **Responsabilidad:** Exponer los insighs al usuario final.
*   **Interacciones:**
    *   **WebApp (Streamlit):** Carga los datos de la capa Gold y permite navegación interactiva.
        *   Realiza consultas RAG (Retrieval-Augmented Generation) en tiempo real para que el usuario pueda "chatear" con su base de datos.
    *   **Dashboard de Salud:** Visualiza métricas de complejidad ciclomática y cobertura de documentación.

## 🔄 Flujo de Información (Data Flow)

1.  **Raw Layer:** La metadata entra como un volcado masivo del servidor.
2.  **Processed Layer:** Se convierte en grafos dirigidos y maestros normalizados.
3.  **Knowledge Layer:** Se enriquece con metadatos semánticos (explicaciones, tags de negocio).
4.  **Gold Layer:** Se consolida en un modelo de datos unificado listo para ser consultado por la UI.
