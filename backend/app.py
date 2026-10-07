from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

from backend.database import Database
from backend.pricing import PricingEngine
from backend.sync_manager import SyncManager
from backend.ide_detector import IDEDetector
from backend.config import BASE_DIR, PRICING_FILE_PATH

db = Database()
pricing = PricingEngine()
sync_manager = SyncManager(db, pricing)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start periodic background sync every 30 seconds
    sync_manager.start_background_sync(interval_seconds=30)
    yield
    sync_manager.stop()

app = FastAPI(
    title="TokenPulse AI | Contador de Tokens & Costes Multi-IDE",
    description="Monitor unificado de consumo y costes de tokens para múltiples IDEs (Antigravity, OpenCode, Claude Code, Cursor, Windsurf, VS Code, Ollama, Continue, Aider) y modelos de IA",
    version="1.3.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = BASE_DIR / "frontend"

@app.get("/api/stats")
def get_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Retorna métricas consolidadas, desglose por IDE, modelo, proyectos y línea temporal, con soporte de filtro de fechas."""
    stats = db.get_summary_stats(start_date=start_date, end_date=end_date)
    stats["last_sync"] = sync_manager.last_sync_result or {
        "timestamp": sync_manager.last_sync_time,
        "status": "idle"
    }
    return stats

@app.get("/api/ides")
def get_ides_status():
    """Retorna lista de todos los IDEs soportados con su estado de detección y consumo acumulado."""
    ides = IDEDetector.get_known_ides()
    stats = db.get_summary_stats()
    by_ide_map = {item["source_ide"].lower(): item for item in stats.get("by_ide", [])}

    for ide in ides:
        ide_stat = by_ide_map.get(ide["id"], {})
        ide["session_count"] = ide_stat.get("sessions", 0)
        ide["tokens_count"] = ide_stat.get("tokens", 0)
        ide["cost_usd"] = ide_stat.get("cost_usd", 0.0)
        if ide["session_count"] > 0:
            ide["status"] = "active"
            ide["status_label"] = "Activo y Auditado"
    return ides

@app.get("/api/projects")
def get_projects():
    """Retorna la lista de todos los proyectos trackeados con sus métricas acumuladas desde el inicio."""
    return db.get_projects_list()

@app.get("/api/projects/{project_name}")
def get_project_detail(
    project_name: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Retorna auditoría completa de un proyecto específico: desglose por cada IA, timeline y sesiones."""
    detail = db.get_project_detail(project_name, start_date=start_date, end_date=end_date)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Proyecto '{project_name}' no encontrado")
    return detail

@app.post("/api/projects/init")
def api_init_project(payload: Dict[str, Any] = Body(...)):
    """Inicializa y vincula un proyecto."""
    from tokenpulse.cli import init_project
    path = payload.get("path", ".")
    name = payload.get("name")
    budget = float(payload.get("budget", 0.0))
    tokens = int(payload.get("tokens", 0))
    res = init_project(target_dir=path, name=name, budget=budget, token_limit=tokens)
    return {"status": "success" if res == 0 else "error"}

@app.post("/api/projects/{project_name}/event")
def api_log_project_event(project_name: str, payload: Dict[str, Any] = Body(...)):
    """Registra un evento o comando ejecutado en el proyecto."""
    desc = payload.get("description", "Actualización")
    cmd = payload.get("command", "")
    model = payload.get("model", "default")
    ide = payload.get("ide", "antigravity")
    tokens = int(payload.get("tokens", 0))

    cost_usd, friendly_model = pricing.calculate_cost(model, tokens, 0) if tokens > 0 else (0.0, model)
    db.add_project_event(
        project_name=project_name,
        event_type="command" if cmd else "process",
        description=desc,
        command_text=cmd,
        model_name=friendly_model,
        tokens_used=tokens,
        cost_usd=cost_usd,
        metadata=f'{{"source_ide": "{ide}"}}'
    )
    return {"status": "success", "cost_usd": cost_usd}

@app.post("/api/projects/scan")
def api_scan_projects(payload: Dict[str, Any] = Body(default={})):
    """Escanea y auto-descubre proyectos en una carpeta raíz."""
    from tokenpulse.cli import scan_projects
    path = payload.get("path")
    discovered = scan_projects(root_dir=path)
    return {"status": "success", "count": len(discovered), "projects": discovered}

@app.get("/api/projects/{project_name}/export")
def api_export_project(project_name: str):
    """Genera y descarga un reporte Markdown completo del proyecto."""
    from tokenpulse.cli import export_project_markdown
    md = export_project_markdown(project_name)
    return PlainTextResponse(content=md, media_type="text/markdown")

@app.get("/api/sessions")
def get_sessions(
    limit: int = Query(50, ge=1, le=200),
    ide: Optional[str] = Query("all"),
    project: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Lista las sesiones filtradas por IDE, proyecto, búsqueda o rango de fechas."""
    return db.list_sessions(
        limit=limit, 
        ide_filter=ide, 
        project_filter=project, 
        search=search,
        start_date=start_date,
        end_date=end_date
    )

@app.post("/api/sync")
def trigger_sync():
    """Fuerza una sincronización manual inmediata de todos los entornos e IDEs."""
    result = sync_manager.sync_all()
    return {"status": "success", "result": result}

@app.get("/api/pricing")
def get_pricing():
    """Obtiene la configuración actual de tarifas por modelo."""
    return pricing.models

@app.post("/api/pricing")
def update_pricing(payload: Dict[str, Any] = Body(...)):
    """Actualiza tarifas personalizadas de modelos."""
    try:
        import json
        with open(PRICING_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump({"models": payload}, f, indent=2)
        pricing.load_pricing()
        return {"status": "success", "message": "Tarifas actualizadas correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend files
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
def serve_index():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Frontend en construcción."}
