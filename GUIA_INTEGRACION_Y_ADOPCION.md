# 🚀 Guía de Integración, Empaquetado y Adopción Externa — TokenPulse AI

Esta guía explica cómo instalar, reutilizar e integrar **TokenPulse AI** en cualquier proyecto de software (Python, Node.js, Ren'Py, Rust, etc.) para medir el consumo de tokens y costes de Inteligencia Artificial.

---

## 📦 1. Instalación y Empaquetado

TokenPulse AI es compatible con los estándares modernos de empaquetado de Python (**PEP 517 / PEP 518**) gracias a su archivo `pyproject.toml`.

### Instalación en modo desarrollo (editable)

```bash
git clone https://github.com/MaciasSM2/TokenPulse-AI.git
cd TokenPulse-AI
pip install -e .
```

### Instalación directa como dependencia en otro proyecto

Puedes agregar TokenPulse directamente en el `requirements.txt` o `pyproject.toml` de tu proyecto:

```txt
# requirements.txt
tokenpulse-ai @ git+https://github.com/MaciasSM2/TokenPulse-AI.git
```

---

## 🛠️ 2. Uso mediante Línea de Comandos (CLI)

Una vez instalado, el comando `tokenpulse` queda disponible globalmente en tu terminal:

| Comando | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `tokenpulse serve` | Inicia el dashboard web y la API REST en tiempo real | `tokenpulse serve --port 4120` |
| `tokenpulse init` | Vincula un repositorio o carpeta a TokenPulse | `tokenpulse init ./mi-proyecto --name "MiApp" --budget 15.0` |
| `tokenpulse status` | Muestra en terminal la auditoría de tokens y costes del proyecto | `tokenpulse status ./mi-proyecto` |
| `tokenpulse log` | Registra una tarea, llamada a IA o actualización | `tokenpulse log "Prompting optimizado" --model gpt-4o --tokens 2500` |
| `tokenpulse scan` | Auto-detecta y vincula proyectos en una carpeta raíz | `tokenpulse scan "C:\Proyectos"` |
| `tokenpulse export` | Exporta un informe ejecutivo del proyecto en formato Markdown | `tokenpulse export "MiApp" --out reporte.md` |
| `tokenpulse cleanup` | Re-consolida subcarpetas y unifica sesiones en sus proyectos raíz | `tokenpulse cleanup` |

---

## 🐍 3. SDK Python para Instrumentar Código en Otros Proyectos

Si tienes un proyecto en Python (un chatbot, un backend FastAPI, un pipeline de LangChain o un juego en Ren'Py), puedes registrar el consumo de tus modelos en 2 líneas de código:

### Opción A: Registro Directo (`track_usage`)

```python
from tokenpulse import track_usage

# Registra una llamada a la API de IA
track_usage(
    model="claude-3-7-sonnet",
    input_tokens=1450,
    output_tokens=320,
    project_name="MiProyecto",
    description="Generación de diálogo interactivo"
)
```

### Opción B: Instancia `TokenTracker`

```python
from tokenpulse import TokenTracker

tracker = TokenTracker(project_name="MiProyecto")

# Registrar evento
tracker.log(
    model="gemini-2.5-pro",
    input_tokens=2100,
    output_tokens=540,
    command="summarize_pdf"
)
```

### Opción C: Decorador Automático para OpenAI / Anthropic

El decorador `@tracker.track()` inspecciona la respuesta del modelo y extrae los tokens (`prompt_tokens`, `completion_tokens`, `reasoning_tokens`) de forma 100% automática:

```python
from tokenpulse import TokenTracker
from openai import OpenAI

tracker = TokenTracker(project_name="ChatBot")
client = OpenAI()

@tracker.track(model="gpt-4o", description="Respuesta a usuario")
def responder(pregunta: str):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": pregunta}]
    )

# Al llamar a la función, el consumo queda registrado automáticamente en TokenPulse
res = responder("¿Cómo optimizar un índice en PostgreSQL?")
```

> [!NOTE]
> **Tolerancia a Fallos:** El SDK de TokenPulse está diseñado para no interrumpir jamás el funcionamiento de tu aplicación. Si el servidor central o la base de datos no están disponibles, almacena el evento localmente en `.tokenpulse/events.jsonl` dentro de la carpeta del proyecto sin arrojar excepciones.

---

## 🛡️ 4. Insignia Dinámica (Badge SVG) para tu `README.md`

Puedes presumir la auditoría de tokens y costes de tu proyecto directamente en tu repositorio de GitHub incrustando la insignia vectorial:

```markdown
[![TokenPulse AI](http://localhost:4120/api/projects/NOVA/badge.svg)](http://localhost:4120/?project=NOVA)
```

**Resultado visual:**

```text
[ TokenPulse AI | 3.1M tok | $5.34 USD ]
```

---

## 📂 5. Explorador Visual de Carpetas y Verificador Inteligente

En el Dashboard web (`http://localhost:4120`):

1. Haz clic en **+ Vincular Proyecto**.
2. Haz clic en **📂 Examinar**: se desplegará el explorador de directorios en vivo.
3. El explorador clasifica en tiempo real cada carpeta:
   - **✅ Proyecto**: Si contiene `.git`, `package.json`, `pyproject.toml`, `requirements.txt`, Ren'Py `game/options.rpy`, etc.
   - **📁 Carpeta**: Si es una carpeta sin descriptores de software.
4. Al hacer clic en **Seleccionar**, el sistema ejecuta la verificación en vivo mostrando el nivel de confianza, las tecnologías detectadas y sugiriendo el nombre canónico del proyecto.

---

## ⭐ 6. Proyectos Favoritos y Control de Visibilidad

- **Favoritos (⭐):** Haz clic en la estrella dorada de cualquier proyecto para anclarlo en la parte superior del listado y en el selector de auditoría.
- **Ocultar / Archivar (👁️):** Descarta carpetas irrelevantes con 1 solo clic. Puedes recuperarlas en cualquier momento desde la pestaña **👁️ Ocultos**.
- **Preferencias de Visibilidad (⚙️ Visibilidad):** Oculta los 7 IDEs desconectados que no utilizas para mantener un espacio de trabajo limpio y enfocado exclusivamente en las herramientas activas.
