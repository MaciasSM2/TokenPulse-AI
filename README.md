# ⚡ TokenPulse AI — Monitor, Auditor & Contador de Tokens por Proyecto

[![Versión](https://img.shields.io/badge/version-1.3.0-00f0ff.svg?style=flat-square)](https://github.com/MaciasSM2/TokenPulse-AI/releases)
[![Python](https://img.shields.io/badge/python-3.10+-3b82f6.svg?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-10b981.svg?style=flat-square)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/database-SQLite_WAL-f59e0b.svg?style=flat-square)](https://www.sqlite.org/)
[![Multi-IDE](https://img.shields.io/badge/entornos-9_IDEs_Auditados-8b5cf6.svg?style=flat-square)](https://github.com/MaciasSM2/TokenPulse-AI)
[![Modelos IA](https://img.shields.io/badge/catálogo-41+_Modelos-ec4899.svg?style=flat-square)](https://github.com/MaciasSM2/TokenPulse-AI)

**TokenPulse AI** es una plataforma unificada de auditoría financiera, monitoreo de telemetría y contabilidad de tokens de Inteligencia Artificial en tiempo real para desarrolladores. Diseñada para trabajar de forma nativa con **Antigravity IDE**, **OpenCode Desktop**, **Claude Code**, **Cursor**, **Windsurf**, **VS Code**, **Continue**, **Aider** y **Ollama Local**, estructurando las métricas **por proyecto**, **por sesión**, **por modelo de IA** y **por ventanas temporales dinámicas**.

---

## 🌟 Novedades de la Versión 1.3.0

### 1. 📅 Filtro Temporal Dinámico y Selector de Fechas

* **Carga Inicial Predeterminada en el Día Presente:** Al abrir el aplicativo web, el sistema se enfoca automáticamente en **"Hoy (Día Presente)"**, permitiendo auditar inmediatamente cuánto se ha gastado en tokens y dólares durante la jornada de trabajo actual.
* **Filtros Rápidos de 1 Clic (Presets):**
  * `⚡ Hoy (Día Presente)`: Sesiones ejecutadas en el día en curso (sincronizado en horario local y UTC).
  * `3 Días`: Consumo acumulado de las últimas 72 horas.
  * `1 Semana (7 días)`: Métricas de los últimos 7 días.
  * `1 Mes (30 días)`: Facturación mensual proyectada de los últimos 30 días.
  * `Todo el Histórico (Ilimitado)`: Auditoría integral desde el primer día registrado (`2026-05-16`) hasta hoy.
* **Selector por Calendario con Retroactividad Ilimitada:** Entradas de fecha `Desde` y `Hasta` con interfaz oscura (`color-scheme: dark`) para consultar cualquier ventana temporal pasada sin restricciones.
* **Métricas KPI Duales:** Las tarjetas muestran los valores del período consultado junto a un sub-indicador comparativo del acumulado histórico total de toda la vida del proyecto.
* **Filtro Aplicable por Proyecto:** Cada ficha de proyecto individual incluye su propia barra de presets para auditar la evolución de un repositorio específico en el rango elegido.

### 2. 🔌 Detección Universal Multi-IDE (9 Entornos en Paralelo)

* **Barra Hub "Entornos e IDEs":** Supervisión visual en vivo con estados de conexión para:
  1. **Antigravity IDE** (Google DeepMind)
  2. **OpenCode Desktop**
  3. **Claude Code** (Anthropic CLI)
  4. **Cursor AI** (Anysphere)
  5. **Windsurf Editor** (Codeium)
  6. **VS Code** (Extensiones Cline, Roo Code, GitHub Copilot)
  7. **Continue.dev** (Extensión Open Source)
  8. **Aider** (Pair Programming CLI)
  9. **Ollama Local AI** (Modelos offline a $0.00 USD)

### 3. 🧠 Catálogo Universal de Modelos de IA

* **Google Gemini:** Gemini 2.5 Pro, 3.8 Flash, 2.0 Flash, 2.0 Flash Thinking, 1.5 Pro, 1.5 Flash.
* **Anthropic Claude:** Claude 3.7 Sonnet (Hybrid Reasoning), Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus.
* **OpenAI:** o1, o3-mini, GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5.
* **DeepSeek:** DeepSeek-V3 (`deepseek-chat`), DeepSeek-R1 (`deepseek-reasoner`), DeepSeek Coder V2.
* **Meta Llama:** Llama 3.3 70B, Llama 3.1 405B, 70B, 8B.
* **Mistral AI:** Codestral 2501, Mistral Large 2, Mistral Small.
* **Alibaba Qwen:** Qwen 2.5 Coder 32B, 7B, Qwen 2.5 72B.
* **Modelos Gratuitos y Offline:** DeepSeek V4 Flash Free, Nemotron 3 Ultra Free, Mimo V2.5 Free, Big Pickle, Ollama local.

### 4. 🚀 Portabilidad Multi-Dispositivo y Auto-Descubrimiento

* **Comando CLI `python -m tokenpulse scan`:** Rastrea y vincula en bloque todos los repositorios dentro de una carpeta raíz de trabajo.
* **Identificador Universal:** Vinculación por URL remota de GitHub (`remote.origin.url`), permitiendo trasladar proyectos entre distintos ordenadores sin romper la auditoría histórica.
* **Exportación en Markdown:** Generación instantánea de informes forenses descargables con desglose completo por IA y cronología.

---

## 🛠️ Arquitectura Multi-IDE Auditada

| Entorno / IDE | Proveedor | Ubicación Auditada | Colector Especializado |
| :--- | :--- | :--- | :--- |
| **Antigravity IDE** | Google DeepMind | `~/.gemini/antigravity-ide/brain/` | `antigravity_collector.py` |
| **OpenCode Desktop** | OpenCode AI | `~/.local/share/opencode/opencode.db` | `opencode_collector.py` |
| **Claude Code** | Anthropic | `~/.claude/` y `.claude.json` | `claude_collector.py` |
| **Cursor AI** | Anysphere | `AppData/Roaming/Cursor/User/workspaceStorage/` | `cursor_collector.py` |
| **Windsurf Editor** | Codeium | `AppData/Roaming/Windsurf/User/workspaceStorage/` | `cursor_collector.py` |
| **VS Code (Cline/Roo)** | VS Code | `AppData/Roaming/Code/User/globalStorage/` | `vscode_collector.py` |
| **Continue.dev** | Open Source | `~/.continue/sessions/` | `continue_collector.py` |
| **Aider Pair** | Open Source | `.aider.chat.history.md` en proyectos | `aider_collector.py` |
| **Ollama Local AI** | Offline | `~/.ollama/models/` | `ollama_collector.py` |

---

## 💻 Instalación y Puesta en Marcha

### 1. Clonar el Repositorio

```bash
git clone https://github.com/MaciasSM2/TokenPulse-AI.git
cd TokenPulse-AI
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Verificar Salud del Sistema

Ejecuta el verificador preventivo para validar la integridad de la base de datos y colectores:

```bash
python check_health.py
```

### 4. Iniciar el Servidor Web Dashboard

```bash
python main.py --port 4120
```

Abre en tu navegador:  
👉 **[http://localhost:4120](http://localhost:4120)**

---

## 📖 Uso del Paquete CLI (`tokenpulse`)

### Auto-Descubrimiento en Masa de Proyectos

Escanea un directorio raíz de proyectos y vincula automáticamente todos los repositorios Git encontrados:

```bash
python -m tokenpulse scan "C:\Users\<TuUsuario>\Documents\0. Programacion"
```

### Vincular un Proyecto Individual

```bash
python -m tokenpulse init "C:\ruta\a\tu\proyecto"
# O dentro del mismo directorio:
python -m tokenpulse init .
```

### Consultar el Estado y Desglose de un Proyecto

```bash
python -m tokenpulse status "C:\ruta\a\tu\proyecto"
```

Muestra en la terminal:

* Tokens totales, de entrada, salida y razonamiento.
* Inversión monetaria acumulada en USD.
* Tabla comparativa de cada IA utilizada con porcentaje de participación y costo individual.

### Registrar un Evento, Comando o Situación Manualmente

```bash
python -m tokenpulse log "Optimización de base de datos" --cmd "python -m alembic upgrade head" --model "gemini-2.5-pro" --tokens 2400
```

---

## 📂 Estructura del Repositorio

```text
TokenPulse-AI/
├── tokenpulse/                  # Paquete CLI portátil y comandos del sistema
│   ├── __init__.py              # Definición de versión v1.3.0
│   ├── __main__.py              # Punto de entrada `python -m tokenpulse`
│   └── cli.py                   # Comandos: init, status, log, scan
├── backend/                     # Motor backend FastAPI y conectores de datos
│   ├── app.py                   # Endpoints REST (stats, projects, sessions, export)
│   ├── config.py                # Rutas del sistema y configuración centralizada
│   ├── database.py              # Esquema SQLite, consultas analíticas y filtros temporales
│   ├── pricing.py               # Motor de tarifas y normalizador multi-modelo
│   ├── ide_detector.py          # Detección y sondeo de los 9 entornos de desarrollo
│   ├── antigravity_collector.py # Conector de transcripciones Antigravity IDE
│   ├── opencode_collector.py    # Conector de base de datos OpenCode Desktop
│   ├── claude_collector.py      # Conector Claude Code CLI
│   ├── cursor_collector.py      # Conector Cursor AI y Windsurf Editor
│   ├── vscode_collector.py      # Conector VS Code (Cline, Roo Code, Copilot)
│   ├── continue_collector.py    # Conector Continue.dev
│   ├── aider_collector.py       # Conector Aider Pair CLI
│   ├── ollama_collector.py      # Conector Ollama Local AI
│   ├── sync_manager.py          # Gestor de sincronización periódica en segundo plano
│   └── pricing_models.json      # Catálogo de precios de 41+ modelos de IA
├── frontend/                    # Interfaz web de usuario (SPA Reactiva)
│   ├── index.html               # Vistas: Global, Proyecto, Hub IDEs, Barra Temporal
│   ├── app.css                  # Estilos glassmorphism, responsive y dark mode
│   └── app.js                   # Lógica reactiva, gráficos y navegación interactiva
├── token_tracker.db             # Base de datos SQLite local unificada
├── check_health.py              # Diagnóstico preventivo y pruebas automáticas
├── main.py                      # Lanzador CLI y servidor uvicorn
├── requirements.txt             # Dependencias de Python
├── DOCUMENTACION_PREVENTIVA.md  # Registro histórico de solicitudes y arquitectura
├── PLAN_CONTADOR_TOKENS.md      # Plan maestro y fases de desarrollo
└── README.md                    # Manual y documentación principal
```

---

## 📄 Historial de Versiones

* **v1.3.0 (2026-10-06):**
  * Implementación del filtro temporal y selector de fechas (`Hoy / 1 Día`, `3 Días`, `1 Semana`, `1 Mes`, `Todo el Histórico`).
  * Modo de inicio predeterminado en el día presente con KPIs duales de período e histórico acumulado.
  * Selector nativo de calendario oscuro con retroactividad ilimitada hasta el inicio del registro histórico.
  * Integración de filtros temporales también en la vista individual por proyecto.
* **v1.2.0 (2026-10-06):**
  * Expansión universal Multi-IDE (9 entornos auditados con detectores y colectores automáticos).
  * Catálogo ampliado a 41+ modelos de IA con tarifas oficiales y desglose por proveedor.
  * Hub de entornos en vivo en el panel superior del Dashboard.
* **v1.1.0 (2026-10-06):**
  * Comando CLI `python -m tokenpulse scan` para auto-descubrimiento masivo de repositorios.
  * Asociación universal independiente de la máquina vía URL de Git Remote (`remote.origin.url`).
  * Endpoint y botón de exportación de reportes de auditoría en Markdown.
* **v1.0.0 (2026-10-06):**
  * Lanzamiento inicial con colectores para Antigravity IDE y OpenCode Desktop.
  * Base de datos unificada SQLite en modo WAL y Dashboard Web con vista global y por proyecto.

---

## ⚖️ Licencia y Autoría

Desarrollado con arquitectura resiliente, modular y portable.  
Código libre bajo la licencia [MIT](LICENSE).
