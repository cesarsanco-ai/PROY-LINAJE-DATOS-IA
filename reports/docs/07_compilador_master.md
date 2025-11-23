## 📄 Documentación Técnica: `src/04_lineage_core/07_compilador_master.py`

### 1\. Descripción General

**¿Qué hace el script?**
Construye el **Maestro de Trazabilidad Total** utilizando una estrategia **Bottom-Up con Memoización**.
En lugar de calcular el linaje cada vez que un usuario pregunta (como hace el script 6), este script pre-calcula el linaje de **todas** las tablas del sistema de una sola vez y lo guarda en un archivo JSON optimizado.

**¿Por qué Memoización?**
En sistemas ETL complejos, muchas tablas intermedias (ej. `Dim_Tiempo`, `Maestro_Clientes`) son reutilizadas por cientos de procesos.

  * **Sin Memoización:** El algoritmo recalcularía el linaje de `Maestro_Clientes` 500 veces.
  * **Con Memoización:** Lo calcula 1 vez, lo guarda en memoria (`cache_trazabilidad`) y reutiliza el resultado instantáneamente para los siguientes 499 procesos. Esto reduce el tiempo de ejecución exponencialmente.

### 2\. Especificaciones de Ejecución

#### 📥 Input (Origen)

  * **Inteligencia:** `metadata/banco_metadata_sp.json` (Datos validados por IA).
  * **Identidad:** `maestros/maestro_tablas.csv` (Nombres oficiales).

#### 📤 Output (Destino)

  * **Archivo Maestro:** `maestro_trazabilidad.json` (El "Cerebro Persistente").
  * **Consola:** Estadísticas de rendimiento y consulta interactiva post-proceso.

-----

### 3\. Lógica Algorítmica

#### Fase 1: Inversión del Grafo

Primero, transforma la metadata centrada en procesos ("Este SP lee A y escribe B") a una estructura centrada en datos ("La tabla B es escrita por el SP X").

  * **Resultado:** Un diccionario `sps_por_tabla`.

#### Fase 2: Construcción Recursiva (Deep Lineage)

Aplica una función recursiva `obtener_trazabilidad_tabla(tabla)`:

1.  **Check Cache:** ¿Ya calculé esto? Si sí $\rightarrow$ Retorno inmediato.
2.  **Check Origen:** ¿Nadie escribe en esta tabla? $\rightarrow$ Es origen (Nivel 0).
3.  **Recursión:** Si hay SPs generadores, llamo a la función para cada uno de sus `inputs`.
4.  **Agregación:** Combino los resultados de los hijos (profundidad máxima, conjunto de tablas origen) y construyo el nodo actual.
5.  **Store Cache:** Guardo el resultado en `cache_trazabilidad`.

-----

### 4\. Estructura del JSON Generado

El archivo `maestro_trazabilidad.json` tiene esta estructura rica para cada tabla:

```json
"STG_VENTAS": {
  "tabla_id": "tb_00102",
  "trazabilidad": {
    "es_origen": false,
    "profundidad": 3,
    "total_sps_generadores": 1,
    "tablas_origen": ["RAW_SAP_VENTAS", "RAW_PRECIOS"],
    "sps_generadores": [
      {
        "sp_id": "SP_0055",
        "sp_nombre": "RTM_OD_CARGAR_VENTAS",
        "inputs_trazabilidad": [ ... ] // Estructura anidada
      }
    ]
  }
}
```

### 5\. Utilidad para la IA Futura

Este archivo es **oro puro** para un Chatbot RAG.
Si un usuario pregunta: *"¿De dónde viene el dato de ventas?"*, la IA no necesita pensar ni ejecutar algoritmos complejos. Solo lee la entrada `"STG_VENTAS"` del JSON y tiene la respuesta completa, pre-validada y lista para narrar.

-----

### 📝 Resumen de Contexto (Prompt para siguiente IA)

> "El script `7_constructor_maestro_trazabilidad.py` es el **Compilador de Linaje**.
>
> **Función:** Pre-calcula y materializa todo el conocimiento de linaje en un único archivo JSON (`maestro_trazabilidad.json`).
> **Algoritmo:** Usa recursividad con memoización para ser eficiente en grafos densos.
>
> **Uso Estratégico:** Este JSON debe ser la fuente de verdad para cualquier dashboard de gobierno de datos o asistente de IA, ya que elimina la latencia de cálculo en tiempo real."