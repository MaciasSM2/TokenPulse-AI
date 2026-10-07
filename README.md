# ⚡ TokenPulse AI — Contador de Tokens & Costes por Proyecto

Monitor unificado, auditor y contador de gasto de Inteligencia Artificial en tiempo real para **Antigravity IDE** y **OpenCode Desktop**, con integración para **Graphify** y **Caveman**, estructurado específicamente **por proyectos** y **por cada modelo de IA**.

---

## 🌟 Características Principales

### 1. Auditoría Específica por Proyectos
- **Seguimiento desde el Inicio hasta la Actualidad:** Historial cronológico completo de la tokenización de cada proyecto desde su primera sesión hasta el día de hoy.
- **Desglose de cada Inteligencia Artificial por Separado:** Tabla detallada en cada proyecto mostrando exactamente qué IAs se utilizaron (*Gemini 2.5 Pro*, *Gemini 3.8 Flash*, *DeepSeek V4 Flash*, *Claude*, etc.), cuántos tokens consumió cada una (entrada, salida y pensamiento) y cuánto dinero se gastó en cada una.
- **Registro de Procesos y Comandos:** Registro cronológico de cada comando, situación o actualización ejecutada en el proyecto.

### 2. Paquete de Integración (`tokenpulse`)
Cualquier carpeta de proyecto puede vincularse y auditarse fácilmente:
- Inicializa el proyecto con `.tokenpulse/config.json` y `.tokenpulse/events.jsonl`.
- Consulta el estado y costos del proyecto directamente desde la terminal.
- Registra comandos o actualizaciones manuales en el historial.

### 3. Dashboard Web en Tiempo Real
- **Vista Global:** Resumen consolidado de todos los entornos, métricas globales, comparativa Antigravity vs OpenCode y ranking de repositorios.
- **Vista por Proyecto:** Panel de control dedicado por proyecto con KPIs, desglose por IAs, línea temporal histórica y explorador de procesos.
- **Modales Interactivos:**
  - Vincular nueva carpeta de proyecto desde la web.
  - Registrar comandos/procesos con cálculo de tokens.
  - Configurar tarifas por millón de tokens por modelo.

---

## 🚀 Uso del Paquete CLI (`tokenpulse`)

### 1. Vincular un Proyecto
Para vincular e inicializar el seguimiento en una carpeta de proyecto:
```bash
python -m tokenpulse init "C:\ruta\a\tu\proyecto"
```
*(O simplemente `python -m tokenpulse init .` dentro de la carpeta del proyecto)*

### 2. Consultar Auditoría y Desglose por IAs de un Proyecto
```bash
python -m tokenpulse status "C:\ruta\a\tu\proyecto"
```
Muestra en consola:
- Tokens totales, de entrada, salida y razonamiento.
- Gasto acumulado en USD.
- **Tabla de cada IA por separado** con sus tokens, porcentaje y coste.
- Historial reciente de fechas activas.

### 3. Registrar un Comando o Proceso en el Proyecto
```bash
python -m tokenpulse log "Refactorización de autenticación" --cmd "npm run build" --model "gemini-3.8-flash" --tokens 1500
```

---

## 🌐 Dashboard Web

### Iniciar el Servidor Web
```bash
python main.py
```
Abre en tu navegador:  
👉 **[http://localhost:4120](http://localhost:4120)**

### Navegación Directa a un Proyecto
Puedes abrir el navegador directamente en la vista de un proyecto específico:
- `http://localhost:4120/?project=CV-AUTO`
- `http://localhost:4120/?project=Grabadora_para_Escritores`
- `http://localhost:4120/?project=ChatBot-Modulo-Saludo`
- `http://localhost:4120/?project=Contador de tokens`

---

## 📁 Estructura del Proyecto

```
Contador de tokens/
├── tokenpulse/                  # Paquete CLI para proyectos
│   ├── __init__.py
│   ├── __main__.py
│   └── cli.py                   # Comandos init, status, log
├── backend/
│   ├── app.py                   # Servidor FastAPI y API de proyectos
│   ├── config.py                # Rutas y configuración
│   ├── database.py              # SQLite con esquema de proyectos y eventos
│   ├── pricing.py               # Motor de tarifas y normalización de IAs
│   ├── opencode_collector.py    # Conector OpenCode Desktop SQLite
│   ├── antigravity_collector.py # Conector Antigravity IDE
│   ├── sync_manager.py          # Gestor de sincronización periódica
│   └── pricing_models.json      # Tarifas por millón de tokens
├── frontend/
│   ├── index.html               # Dashboard con vista global y vista por proyecto
│   ├── app.css                  # Estilos dark mode y glassmorphism
│   └── app.js                   # Lógica reactiva y navegación entre proyectos
├── token_tracker.db             # Base de datos local consolidada
├── main.py                      # Lanzador CLI y servidor web
├── PLAN_CONTADOR_TOKENS.md      # Plan de arquitectura
└── README.md                    # Documentación del proyecto
```
