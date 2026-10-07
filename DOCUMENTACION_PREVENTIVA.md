# 🛡️ Documentación Preventiva y Manual de Resiliencia ante Interrupciones

> [!IMPORTANT]
> **Propósito:** Esta documentación preventiva garantiza que el sistema **TokenPulse AI** (Contador y Auditor de Tokens y Costes) mantenga su integridad y pueda recuperarse de inmediato sin pérdida de datos en caso de apagones imprevistos del equipo, reinicios forzados, fallos de energía o cierres inesperados de aplicaciones.

---

## 1. Arquitectura de Resiliencia (¿Por qué no se pierden los datos?)

El sistema fue diseñado con una arquitectura **idempotente y tolerante a fallos**:

```mermaid
graph TD
    A[Apagón / Cierre Inesperado] --> B{Reinicio del Sistema}
    B --> C[Fuentes de Datos Intactas]
    C --> D[OpenCode SQLite: WAL Mode]
    C --> E[Antigravity Logs: JSONL Append-Only]
    
    B --> F[token_tracker.db: ACID Compliant]
    F --> G[sync_state: Registro de último mtime]
    
    D --> H[SyncManager Reanuda Automáticamente]
    E --> H
    G --> H
    H --> I[Estado 100% Recuperado sin Duplicados]
```

### Principios de Protección de Datos Implementados:
1. **Modo de Lectura Aislado (`mode=ro`):**
   * Al consultar `~/.local/share/opencode/opencode.db`, el colector usa conexiones de solo lectura con URI SQLite. Nunca bloquea ni corrompe la base de datos de OpenCode, incluso si OpenCode se apaga a mitad de escritura.
2. **Idempotencia de Sincronización (`sync_state` & `ON CONFLICT DO UPDATE`):**
   * Si el equipo se apaga a mitad de un proceso de sincronización, la tabla `sync_state` solo actualiza el puntero de archivo (`mtime`) cuando la sesión fue almacenada exitosamente. Al reiniciar, el sistema reanuda exactamente donde se interrumpió sin generar duplicados.
3. **Persistencia Local Descentralizada por Proyecto:**
   * Cada proyecto vinculado guarda su propio archivo local en `.tokenpulse/config.json` y `.tokenpulse/events.jsonl`, de modo que el historial del proyecto existe tanto dentro de su propia carpeta como en la base de datos central `token_tracker.db`.

---

## 2. Protocolo Rápido de Recuperación tras un Apagón

Si tu equipo se apagó repentinamente o se cerró la consola, sigue estos 3 pasos:

### Paso 1: Ejecutar Diagnóstico de Salud
Abre tu terminal en la carpeta del proyecto y ejecuta:
```powershell
python check_health.py
```
* **Qué hace:** Verifica la integridad física de SQLite (`PRAGMA integrity_check`), comprueba la accesibilidad de OpenCode y Antigravity, valida el puerto 4120 y ejecuta una sincronización de prueba.
* **Resultado esperado:** `✅ ESTADO GENERAL: SISTEMA 100% OPERATIVO Y RESILIENTE`.

### Paso 2: Iniciar el Servidor Dashboard
```powershell
python main.py
```
*(O si solo deseas consultar los números en terminal sin abrir el navegador: `python main.py --sync-only`)*

### Paso 3: Abrir el Dashboard en el Navegador
Accede a:
👉 **[http://localhost:4120](http://localhost:4120)**

---

## 3. Matriz de Resolución de Problemas (Troubleshooting)

| Síntoma o Error | Causa Probable | Solución Inmediata |
| :--- | :--- | :--- |
| **Error: `[WinError 10048]` Solo se permite un uso de cada dirección de socket** | Un proceso de Python anterior quedó bloqueando el puerto 4120 tras el corte. | Ejecuta en PowerShell para liberar el puerto:<br>`Get-Process python -ErrorAction SilentlyContinue \| Stop-Process -Force`<br>O arranca en otro puerto: `python main.py --port 4125`. |
| **Error: `[WinError 32]` Proceso no tiene acceso al archivo `token_tracker.db`** | El archivo quedó con un lock activo de Windows. | Cierra procesos huérfanos de Python con:<br>`taskkill /F /IM python.exe`<br>Y vuelve a arrancar con `python main.py`. |
| **Faltan sesiones recientes tras un reinicio** | Los archivos de logs no se habían sincronizado en memoria antes del apagón. | Haz clic en el botón **"Sincronizar"** en la esquina superior derecha del Dashboard o ejecuta `python main.py --sync-only`. |
| **La base de datos se reporta dañada (`PRAGMA integrity_check != ok`)** | Daño severo en el disco durante el corte de corriente. | La base central es un índice consolidado regenerable. Solo elimina `token_tracker.db` y ejecuta `python main.py`: regenerará el 100% de los datos desde las fuentes originales en segundos. |

---

## 4. Directorio de Archivos Críticos y Rutas

| Archivo / Directorio | Ubicación en el Equipo | Función y Criticidad |
| :--- | :--- | :--- |
| **Base Central del Tracker** | `c:\...\Contador de tokens\token_tracker.db` | **Crítico:** Contiene todas las sesiones normalizadas, proyectos registrados y eventos de comandos. |
| **Tarifas de Modelos** | `c:\...\Contador de tokens\backend\pricing_models.json` | **Configuración:** Precios en USD por millón de tokens para cada modelo de IA. |
| **Base Original OpenCode** | `C:\Users\Sebastian Macias\.local\share\opencode\opencode.db` | **Fuente Externa:** Historial nativo de OpenCode Desktop. |
| **Logs Originales Antigravity** | `C:\Users\Sebastian Macias\.gemini\antigravity-ide\brain\` | **Fuente Externa:** Transcripciones de sesiones y llamadas a herramientas. |
| **Paquete por Proyecto** | `<CarpetaDelProyecto>\.tokenpulse\config.json` | **Descentralizado:** Identificador canónico y límites de presupuesto del proyecto. |
| **Diagnóstico de Salud** | `c:\...\Contador de tokens\check_health.py` | **Mantenimiento:** Script para validación rápida en 1 comando. |

---

## 5. Registro de Estado Vivo del Proyecto (Changelog de Solicitudes)

> [!NOTE]
> Esta sección se actualizará continuamente con cada nueva solicitud para mantener trazabilidad exacta de los módulos activos.

### 📌 Solicitud 1: Creación del Núcleo de TokenPulse AI
* **Fecha:** 2026-10-06 19:32
* **Objetivo:** Contador de tokens de gasto para Antigravity IDE y OpenCode Desktop, con instalación de Graphify y Caveman.
* **Componentes Implementados:**
  * Colectores `OpenCodeCollector` y `AntigravityCollector`.
  * Instalación de `graphifyy` (v0.9.79) y `JuliusBrussee/caveman` (v3.1).
  * Backend FastAPI con base de datos SQLite y servidor Uvicorn.
  * Dashboard web inicial en tiempo real.

### 📌 Solicitud 2: Contabilidad Específica por Proyectos e IAs Desglosadas
* **Fecha:** 2026-10-06 20:11
* **Objetivo:** Contabilidad por proyectos, paquete modular para carpetas, vista dedicada en la app con cada IA por separado y línea temporal histórica.
* **Componentes Implementados:**
  * Paquete modular CLI `tokenpulse` (`init`, `status`, `log`).
  * Tablas `registered_projects` y `project_events` en SQLite.
  * Selector interactivo de proyectos en la interfaz web.
  * Tabla **"Inteligencias Artificiales en este Proyecto"** con desglose por cada IA (Gemini, DeepSeek, Claude, etc.) de tokens in/out/thinking y coste en USD.
  * Gráfico temporal histórico del proyecto desde su inicio hasta hoy.
  * Modales web para vincular proyectos y registrar comandos manuales.

### 📌 Solicitud 3: Documentación Preventiva y Diagnóstico Automático
* **Fecha:** 2026-10-06 20:41
* **Objetivo:** Protección contra apagones, interrupciones o salidas accidentales, con protocolo de recuperación y actualización viva en cada iteración.
* **Componentes Implementados:**
  * Creación de `check_health.py` (diagnóstico automático de SQLite, fuentes externas, puertos y sincronización).
  * Redacción de `DOCUMENTACION_PREVENTIVA.md` con matriz de contingencia y guías de recuperación.
  * Protocolo de mantenimiento de estado vivo para futuras solicitudes.

### 📌 Solicitud 4: Publicación y Versionado en GitHub
* **Fecha:** 2026-10-06 21:06
* **Objetivo:** Creación y publicación del repositorio público en GitHub con control de versiones.
* **Componentes Implementados:**
  * Creación de `.gitignore` optimizado para excluir bases de datos locales y temporales.
  * Archivo `requirements.txt` para reproducción exacta de dependencias.
  * Inicialización del repositorio Git local con rama `main`.
  * Publicación remota en GitHub con visibilidad pública (`gh repo create`).

### 📌 Solicitud 5: Portabilidad Multi-Dispositivo y Auto-Descubrimiento
* **Fecha:** 2026-10-06 22:10
* **Objetivo:** Arquitectura para traslado entre computadores, ubicación óptima de proyectos y auto-descubrimiento.
* **Componentes Implementados:**
  * Comando CLI `python -m tokenpulse scan` y botón web para auto-descubrir y vincular proyectos en masa.
  * Identificador universal e independiente de la máquina vía Git Remote URL (`git config --get remote.origin.url`).
  * Endpoint y botón para exportar reportes de auditoría en Markdown (`/api/projects/{name}/export`).
  * Manual de traslado y alojamiento de proyectos en nuevos dispositivos.

---

## 6. Guía de Portabilidad: Traslado a Nuevos Computadores

### A. ¿Dónde deben alojarse los proyectos?
Para garantizar máxima eficiencia, se aconseja mantener una **carpeta raíz unificada de desarrollo**:
* **En Windows:** `C:\Users\<TuUsuario>\Documents\0. Programacion\` o `C:\Proyectos\`
* **En Linux/Mac:** `~/Documents/Proyectos/` o `~/Developer/`

Cada proyecto individual debe residir en su propia subcarpeta con su repositorio Git (ej: `CV-AUTO/`, `NOVA/`, `Grabadora_para_Escritores/`).

### B. ¿Cómo viaja la contabilidad si cambias de equipo?
1. **El Paquete Embebido (`.tokenpulse/`):**
   * Al hacer `git push` y `git pull` de tus proyectos, la carpeta `.tokenpulse/` viaja con el código fuente en GitHub.
2. **Identificador Portátil:**
   * TokenPulse asocia cada proyecto a su URL de GitHub (`https://github.com/Usuario/Repo.git`), por lo que no importa si la ruta absoluta de Windows cambia de `C:\Users\Sebastian\...` a `C:\Users\Otro\...`.
3. **Auto-Descubrimiento en 1 Clic:**
   * Al descargar o clonar TokenPulse en un nuevo computador, simplemente ejecuta:
     ```powershell
     python -m tokenpulse scan "C:\ruta\donde\tienes\tus\proyectos"
     ```
   * O en el Dashboard Web, presiona el botón **"Escanear Proyectos"**. El sistema detectará automáticamente todos los repositorios y reconstruirá la auditoría en 1 segundo.



---

### 📌 Solicitud 6: Expansión Multi-Modelo y Multi-IDE (Auditoría Universal de IA)
* **Fecha:** 2026-10-06 22:55
* **Objetivo:** Extender TokenPulse AI más allá de Antigravity y OpenCode, incorporando todas las inteligencias artificiales modernas y todos los IDEs y entornos de desarrollo AI detectables en el flujo de trabajo.
* **Componentes Implementados:**
  * **Catálogo de 41+ Modelos de IA:**
    * OpenAI (o1, o3-mini, GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5).
    * Anthropic Claude (Claude 3.7 Sonnet con Hybrid Reasoning, Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus).
    * Google Gemini (Gemini 2.5 Pro, 3.8 Flash, 2.0 Flash, 2.0 Flash Thinking, 1.5 Pro, 1.5 Flash).
    * DeepSeek (DeepSeek-V3 `deepseek-chat`, DeepSeek-R1 `deepseek-reasoner`, DeepSeek Coder V2).
    * Meta Llama (Llama 3.3 70B, Llama 3.1 405B, 70B, 8B).
    * Mistral AI (Codestral 2501, Mistral Large 2, Mistral Small).
    * Alibaba Qwen (Qwen 2.5 Coder 32B, 7B, Qwen 2.5 72B).
    * Ollama / Local ($0.00 USD para inferencia offline en hardware local).
    * Modelos Gratuitos (DeepSeek V4 Flash Free, Nemotron 3 Ultra Free, Mimo V2.5 Free, Big Pickle).
  * **Arquitectura de Detección y Colectores Multi-IDE:**
    * `backend/ide_detector.py`: Servicio de detección que audita Antigravity, OpenCode, Claude Code, Ollama, VS Code (Cline/Roo/Copilot), Cursor, Windsurf, Continue.dev y Aider.
    * Colectores especializados: `ClaudeCodeCollector`, `ContinueCollector`, `AiderCollector`, `CursorWindsurfCollector`, `VSCodeAICollector`, `OllamaCollector`.
    * Integración centralizada en `SyncManager.sync_all()`.
  * **Interfaz Web Mejorada (Dashboard 1.2):**
    * **Barra Hub "Entornos e IDEs Detectados":** Monitoreo en vivo de los 9 entornos con estado de conexión, insignias de colores y filtro instantáneo.
    * **Modal de Tarifas con Pestañas por Proveedor:** Filtrado interactivo por proveedor de IA (Google, Anthropic, OpenAI, DeepSeek, Meta, Mistral, Qwen, Ollama, Gratuitos).
    * **Soporte de Registro Manual Multi-IDE:** Registro de eventos vinculados a cualquier IDE y modelo.

---

## 7. Arquitectura Multi-IDE y Colectores Disponibles

| Entorno / IDE | Proveedor / Tipo | Ruta Auditada | Colector |
| :--- | :--- | :--- | :--- |
| **Antigravity IDE** | Google DeepMind | `~/.gemini/antigravity-ide/brain/` | `antigravity_collector.py` |
| **OpenCode Desktop** | OpenCode AI | `~/.local/share/opencode/opencode.db` | `opencode_collector.py` |
| **Claude Code** | Anthropic | `~/.claude/` y `.claude.json` | `claude_collector.py` |
| **Ollama Local AI** | Offline Runtime | `~/.ollama/models/` | `ollama_collector.py` |
| **VS Code (Cline / Roo)** | Extensión VS Code | `AppData/Roaming/Code/User/globalStorage/` | `vscode_collector.py` |
| **Cursor AI** | Anysphere | `AppData/Roaming/Cursor/User/workspaceStorage/` | `cursor_collector.py` |
| **Windsurf Editor** | Codeium | `AppData/Roaming/Windsurf/User/workspaceStorage/` | `cursor_collector.py` |
| **Continue.dev** | Open Source | `~/.continue/sessions/` | `continue_collector.py` |
| **Aider Pair** | CLI Pair Tool | `.aider.chat.history.md` en proyectos | `aider_collector.py` |

---

## 8. Verificación y Pruebas del Sistema
Para validar que todos los colectores, la base de datos y el servidor web funcionan perfectamente:
```powershell
python check_health.py
```
Salida esperada: `5/5 verificaciones superadas con éxito`, reportando estado 100% operativo.

---

### 📌 Solicitud 7: Filtro Temporal y Selector de Fechas (Auditoría por Día y Rango Histórico)
* **Fecha:** 2026-10-06 23:25
* **Objetivo:** 
  1. Mostrar de forma predeterminada al abrir la aplicación el **consumo del día actual (Hoy / Día Presente)** en tokens y costos.
  2. Ofrecer un selector de calendario con rango de fechas (`Desde` / `Hasta`) con retroactividad ilimitada hasta el inicio del registro histórico del proyecto.
  3. Proveer filtros rápidos de un solo clic para **1 Día (Hoy)**, **3 Días**, **1 Semana (7 días)**, **1 Mes (30 días)** y **Todo el Histórico (Ilimitado)**.
* **Componentes Implementados:**
  * **Motor de Consultas y Base de Datos (`backend/database.py`):**
    * Integración de parámetros `start_date` y `end_date` (`YYYY-MM-DD`) en `get_summary_stats`, `get_project_detail` y `list_sessions`.
    * Doble cálculo estadístico:
      * `overall`: métricas agregadas del período seleccionado.
      * `lifetime`: métricas históricas totales de toda la vida del proyecto para contraste inmediato.
      * `today_stats`: desglose específico del día en curso.
      * `date_bounds`: descubrimiento dinámico de la fecha mínima (`2026-05-16`), fecha máxima (`2026-10-07`), fecha local del sistema y fecha UTC.
    * Filtrado cruzado de gráficos de línea temporal (`timeline`), distribución por modelo, entornos/IDEs y tabla de sesiones.
  * **Endpoints de API (`backend/app.py`):**
    * Parámetros query `start_date` y `end_date` admitidos en `/api/stats`, `/api/projects/{project_name}` y `/api/sessions`.
  * **Diseño e Interfaz Web (`frontend/index.html`, `frontend/app.css`, `frontend/app.js`):**
    * **Barra de Rango Temporal Glassmorphism:**
      * Botones de preset rápido con iluminación de estado activo (`⚡ Hoy (Día Presente)`, `3 Días`, `1 Semana`, `1 Mes`, `Todo el Histórico`).
      * Entradas de calendario adaptativas con esquema oscuro (`color-scheme: dark`) con validación de límites automáticos `min` y `max`.
      * Botón `Aplicar Rango` y píldora informativa dinámica `#dateActivePill` con badge de período auditado.
    * **Carga Inicial Enfocada en el Día Presente:**
      * Al abrir TokenPulse AI, el filtro arranca automáticamente en modo `today`, auditando las sesiones generadas en la jornada actual y mostrando en las tarjetas KPI el gasto del día junto a un sub-texto comparativo con el acumulado histórico total.
    * **Filtros Temporales en Vista de Proyecto:**
      * Presets reactivos (`#projPresetButtons`) también disponibles al inspeccionar proyectos individuales, recalculando eventos, modelos y tendencias dentro de la ventana de tiempo elegida.

---

## 9. Resumen de Presets Temporales Disponibles

| Preset | Rango de Días | Finalidad | Comportamiento en Carga |
| :--- | :--- | :--- | :--- |
| **⚡ Hoy (1 Día)** | Día presente (Local / UTC) | Auditar el costo y volumen de tokens de la jornada actual de trabajo. | **Predeterminado al abrir el aplicativo** |
| **3 Días** | Últimas 72 horas | Revisar el progreso reciente del sprint o fin de semana. | Reactivo al clic |
| **1 Semana** | Últimos 7 días | Control semanal de presupuesto y productividad de código. | Reactivo al clic |
| **1 Mes** | Últimos 30 días | Facturación mensual proyectada y comparativa por modelo. | Reactivo al clic |
| **Todo el Histórico** | Desde `2026-05-16` hasta hoy | Panorama global completo y acumulado del desarrollador. | Ilimitado |
| **Personalizado (Calendario)** | Rango libre `Desde` - `Hasta` | Auditoría forense de fechas o entregas específicas. | Ilimitado |

---

## 10. Publicación y Despliegue de Versión v1.3.0 en GitHub

* **Versión Oficial del Sistema:** `v1.3.0`
* **Archivos con Versión Sincronizada:**
  * `tokenpulse/__init__.py`: `__version__ = "1.3.0"`
  * `backend/app.py`: `version="1.3.0"`
  * `frontend/index.html` y `frontend/app.css`: Badge visual interactivo `<span class="badge-version">v1.3.0</span>` en el encabezado.
  * `README.md`: Documentación completa reescrita y actualizada con insignias, arquitectura multi-IDE, catálogo de 41+ modelos y manual de filtros temporales.
  * `PLAN_CONTADOR_TOKENS.md`: Actualización de estado al 100% completado en todas las fases (Fases 1 a 7).
* **Control de Versiones y Release Remoto:**
  * Git Tag: `v1.3.0`
  * GitHub Release: Creado y publicado con `gh release create v1.3.0` en el repositorio [MaciasSM2/TokenPulse-AI](https://github.com/MaciasSM2/TokenPulse-AI).

---

## 11. Solicitud 8 — Explorador de Disco, Verificador Anti-Falsos Positivos, Favoritos, Ocultar Carpetas, Configuración de Visibilidad y Empaquetado para Adopción Externa

* **Fecha de Implementación:** 2026-10-07
* **Contexto y Problemática:**
  1. **Falsos Positivos en Detección de Proyectos:** Subdirectorios de código (`frontend/src/components`, `game/images/world`, `whatsapp-backend/src`) o archivos individuales (`.md`) se registraban incorrectamente como proyectos separados al interactuar con IDEs como OpenCode Desktop.
  2. **Ausencia de Explorador en Disco:** El usuario requería poder navegar interactivamente por las carpetas del sistema para seleccionar la ruta exacta de cualquier proyecto y validarla antes de vincularla.
  3. **Sobrecarga Visual en IDE Hub y Modelos:** Múltiples entornos desconectados (7 IDEs sin actividad como Claude, Cursor, Windsurf, Continue, Aider) ocupaban espacio visual innecesario en la pantalla.
  4. **Adopción y Reutilización Externa:** El sistema debía poder ser descargado, instalado vía `pip` e integrado con 2 líneas de código en proyectos externos (Python, Ren'Py, FastAPI, scripts de IA).
* **Soluciones Implementadas:**
  * **Motor Canónico y Verificador de Proyectos (`backend/project_verifier.py`):**
    * Función `resolve_canonical_project(path)`: Escala el árbol de directorios buscando raíces reales (`.git`, `.tokenpulse`, `package.json`, `Cargo.toml`, Ren'Py `game/options.rpy`, etc.).
    * Función `verify_project_folder(path)`: Calcula un puntaje de confianza (0-100%), stack tecnológico (`Git • Ren'Py • Python • Node`) y descriptores válidos.
    * Función `scan_directory_candidates(path)`: Explorador que audita y clasifica subcarpetas en tiempo real.
  * **Base de Datos y Consolidación (`backend/database.py`):**
    * Columnas agregadas a `registered_projects`: `is_favorite`, `is_hidden`, `is_verified`, `tech_stack`.
    * Función `consolidate_database()`: Reclasificó y unificó 17 sesiones dispersas en subcarpetas a sus proyectos raíz canónicos (`Proyecto 1`, `Grabadora_para_Escritores`, `ChatBot-Modulo-Saludo`).
    * Métodos `toggle_favorite(name)` y `toggle_hidden(name)` para alternar estados al instante.
  * **API REST (`backend/app.py`):**
    * `GET /api/filesystem/browse`: Exploración en vivo de directorios.
    * `POST /api/filesystem/verify`: Verificación algorítmica de carpetas.
    * `POST /api/projects/{name}/favorite`: Alternar favorito ⭐.
    * `POST /api/projects/{name}/hide`: Alternar ocultar/archivar 👁️.
    * `POST /api/projects/cleanup`: Forzar re-consolidación de base de datos.
    * `GET /api/projects/{name}/badge.svg`: Insignia vectorial SVG lista para incrustar en `README.md`.
  * **Interfaz de Usuario Reactiva (`frontend/`):**
    * **Modal de Visibilidad (`#visibilityModal`):**
      * Interruptor maestro para ocultar IDEs desconectados/inactivos con 1 toque.
      * Cuadrícula de checkboxes individuales para los 9 IDEs soportados.
      * Toggles para ocultar modelos no utilizados y mostrar/ocultar proyectos archivados.
      * Persistencia en `localStorage`.
    * **Explorador Visual en Modal de Vinculación (`#folderBrowserBox`):**
      * Navegación hacia arriba y hacia adentro por el árbol de directorios.
      * Badges de proyecto detectado (`✅ Proyecto`) vs carpeta simple (`📁 Carpeta`).
      * Botón `Seleccionar` con auto-relleno y cálculo de score de confianza en vivo.
    * **Pestañas y Acciones de Proyectos:**
      * Pestañas `📁 Todos`, `⭐ Favoritos`, `👁️ Ocultos`.
      * Botón ⭐ para anclar proyectos favoritos al tope de la lista y en el selector.
      * Botón 👁️ para descartar carpetas que no se desean ver sin perder su historial.
  * **Empaquetado y SDK de Medición (`pyproject.toml`, `tokenpulse/tracker.py`):**
    * Configuración PEP 517/518 lista para `pip install -e .`.
    * SDK Python con clase `TokenTracker`, helper `track_usage` y decorador `@tracker.track()` tolerante a fallos.
    * Comandos CLI ampliados: `tokenpulse serve` y `tokenpulse cleanup`.
    * Documentación completa en `GUIA_INTEGRACION_Y_ADOPCION.md`.


