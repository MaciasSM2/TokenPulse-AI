# Plan de Desarrollo: Contador de Tokens y Costes de IA
**Entornos objetivo:** Antigravity IDE & OpenCode Desktop  
**Herramientas de optimización:** Graphify (`graphifyy`) & Caveman  

---

## 1. Estado de Instalación de Herramientas Solicitadas

Ambas herramientas de optimización y ahorro de tokens han quedado instaladas y configuradas en el sistema:

| Herramienta | Versión / Origen | Configuración en Antigravity | Configuración en OpenCode |
| :--- | :--- | :--- | :--- |
| **Graphify** | `graphifyy` v0.9.79 (Python/uv) | `.agents/rules/graphify.md`, `.agents/workflows/graphify.md` y `.agents/skills/graphify` | `.opencode/plugins/graphify.js` (hook `tool.execute.before`) y regla en `AGENTS.md` |
| **Caveman** | `JuliusBrussee/caveman` (v3.1) | `.agents/skills/caveman/SKILL.md` integrado en el espacio de trabajo | `.config/opencode/plugins/caveman`, 9 skills, 8 comandos (`/caveman`, `/caveman-stats`, etc.) y `opencode.jsonc` |

---

## 2. Hallazgos Técnicos de los IDEs en su Equipo

Tras la inspección local en su sistema Windows, se identificaron con exactitud los puntos de conexión y datos disponibles:

### A. OpenCode Desktop
* **Ubicación local:** `C:\Users\Sebastian Macias\.local\share\opencode\opencode.db` (Base de datos SQLite activa).
* **Estructura encontrada:**
  * Tabla `session`: Almacena métricas nativas y exactas: `tokens_input`, `tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`, `cost`, `model`, `directory`, `time_created`, `time_updated`.
  * Tabla `message`: Guarda cada turno con marcas de tiempo individuales y metadatos de modelo.
* **Diagnóstico actual verificado en su máquina:**
  * **130 sesiones** registradas actualmente.
  * **15,884,675 tokens de entrada** y **1,840,578 tokens de salida**.
  * Modelos registrados: DeepSeek V4 Flash, Big Pickle, Nemotron, Mimo, etc.

### B. Antigravity IDE
* **Ubicación local:** 
  * `C:\Users\Sebastian Macias\.gemini\antigravity-ide\brain\<conversation-id>\.system_generated\logs\transcript_full.jsonl`
  * `C:\Users\Sebastian Macias\.gemini\antigravity-ide\conversations\<conversation-id>.db`
* **Estructura encontrada:**
  * **118 conversaciones** históricas en `brain/`.
  * Los archivos `transcript_full.jsonl` registran cronológicamente cada paso: inputs de usuario (`USER_INPUT`), respuestas del modelo (`PLANNER_RESPONSE` con pensamiento `thinking` y llamadas a herramientas `tool_calls`), salidas de ejecución (`RUN_COMMAND`, `VIEW_FILE`), y cambios de configuración de modelo (`USER_SETTINGS_CHANGE`, ej. Gemini 3.8 Flash, Gemini 2.5 Pro).
* **Mecanismo de captura:** Dado que Antigravity no almacena un contador monetario en crudo de fábrica, se calculan tokens mediante un motor BPE/tokenizador rápido sobre los eventos del transcript y se aplican las tarifas oficiales de Gemini (Flash/Pro) y modelos asociados.

---

## 3. ¿Para qué Servirá Específicamente el Proyecto?

1. **Visibilidad Financiera Unificada:** Dashboard único que consolida el gasto y tokens consumidos tanto en Antigravity IDE como en OpenCode Desktop sin depender de interfaces separadas.
2. **Medición del Ahorro (ROI) con Graphify y Caveman:** Gráficas comparativas de gasto por sesión antes y después de activar Caveman (compresión de respuestas) y Graphify (navegación AST para evitar lecturas masivas de archivos).
3. **Presupuestos y Alertas en Tiempo Real:** Alertas visuales o notificaciones cuando una sesión o jornada sobrepase un umbral configurado (ej. 500k tokens o $2.00 USD).
4. **Desglose Multidimensional:**
   * Por Proyecto/Directorio de trabajo.
   * Por Modelo (Gemini Flash vs Pro vs DeepSeek vs Claude).
   * Por Tipo de Token (Input, Output, Reasoning/Thinking, Cache Read/Write).
   * Línea de tiempo (hoy, últimos 7 días, mensual).

---

## 4. Arquitectura Propuesta del Contador de Tokens

```mermaid
graph TD
    A[OpenCode Desktop] -->|Lectura SQLite Directa| B(OpenCode Adapter)
    C[Antigravity IDE] -->|Parser JSONL / SQLite| D(Antigravity Adapter)
    
    B --> E[Motor de Normalización y Agregación]
    D --> E
    
    F[Matriz de Precios de Modelos] --> E
    
    E --> G[(Base de Datos Local: token_counter.db)]
    
    G --> H[API / Sync Engine Local - FastAPI / Node]
    H --> I[Dashboard Web Interactivo]
```

### Componentes Clave:
1. **Colector OpenCode (`opencode_collector.py`):**
   * Conexión de solo lectura en modo WAL a `~/.local/share/opencode/opencode.db`.
   * Extracción de sesiones y sumatorias instantáneas.
2. **Colector Antigravity (`antigravity_collector.py`):**
   * Observador de la carpeta `~/.gemini/antigravity-ide/brain/`.
   * Lector incremental de `transcript_full.jsonl`.
   * Motor de tokenización (utilizando `tiktoken` / tokenizador por BPE o ratio ponderado de caracteres por token) que cuantifica tokens de entrada (contexto + prompts + outputs de herramientas) y tokens de salida (pensamiento + texto generado).
3. **Motor de Tarifas (`pricing_engine.json`):**
   * Tabla configurable con el costo por millón de tokens para cada modelo (Gemini 2.5 Pro, Gemini 3.8 Flash, DeepSeek V4, Claude 3.5, etc.).
4. **Almacén Unificado (`token_tracker.db`):**
   * Base de datos local SQLite ligera que unifica eventos, sesiones, fechas, proyectos y costos calculados.
5. **Dashboard Visual (Frontend):**
   * Interfaz web moderna (modo oscuro, diseño reactivo, gráficos de barras/líneas, métricas KPI destacadas).

---

## 5. Fases de Implementación Sugeridas

### Fase 1: Prototipo de Ingesta y Extracción (Backend Core)
* Crear los módulos extractores para OpenCode y Antigravity.
* Implementar cálculo de tokens y asociación de precios por modelo.
* Probar la agregación con los datos históricos ya existentes en su máquina.

### Fase 2: Almacenamiento Unificado y Sincronizador Automático
* Diseñar la base de datos unificada local (`token_counter.db`).
* Implementar sincronización periódica (detección de nuevas sesiones y actualización incremental en tiempo real).

### Fase 3: API Local y Servidor de Métricas
* Servicio local ligero con endpoints para estadísticas:
  * `/api/summary` (totales acumulados, gasto de hoy, tokens totales).
  * `/api/by-ide` (comparativa Antigravity vs OpenCode).
  * `/api/by-project` (gasto por proyecto/repositorio).
  * `/api/timeline` (evolución por días/horas).

### Fase 4: Dashboard Interactivo y Panel de Control
* Vista visual de alto impacto con KPIs:
  * Gasto estimado en USD.
  * Tokens de entrada, salida y razonamiento.
  * Porcentaje de ahorro estimado por uso de Caveman y Graphify.
  * Filtros por fecha y proyecto.
