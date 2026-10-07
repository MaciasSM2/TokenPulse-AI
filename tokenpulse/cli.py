import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Ensure backend can be imported
APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from backend.database import Database, clean_project_name
from backend.pricing import PricingEngine
from backend.sync_manager import SyncManager

# Windows UTF-8 stdout fix
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_git_remote_url(dir_path: Path) -> Optional[str]:
    """Obtiene la URL remota de Git si existe, para tener un identificador portátil entre máquinas."""
    try:
        res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=str(dir_path),
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None

def init_project(target_dir: str = ".", name: str = None, budget: float = 0.0, token_limit: int = 0):
    proj_path = Path(target_dir).resolve()
    if not proj_path.exists():
        print(f"[Error] La ruta especificada no existe: {proj_path}")
        return 1

    canonical_name = name or clean_project_name(None, str(proj_path))
    git_url = get_git_remote_url(proj_path)

    tokenpulse_dir = proj_path / ".tokenpulse"
    tokenpulse_dir.mkdir(exist_ok=True)

    config_file = tokenpulse_dir / "config.json"
    config_data = {
        "project_name": canonical_name,
        "project_path": str(proj_path),
        "git_remote_url": git_url or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "budget_limit_usd": budget,
        "token_limit": token_limit,
        "tracked_ides": ["antigravity", "opencode"]
    }

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    events_file = tokenpulse_dir / "events.jsonl"
    if not events_file.exists():
        with open(events_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "init",
                "description": "Proyecto inicializado y vinculado con TokenPulse AI",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "git_url": git_url
            }) + "\n")

    # Register in central database
    db = Database()
    db.register_project(canonical_name, str(proj_path), budget=budget, token_limit=token_limit)
    db.add_project_event(
        project_name=canonical_name,
        event_type="init",
        description="Proyecto vinculado con TokenPulse AI",
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata=json.dumps({"git_url": git_url})
    )

    print("=" * 65)
    print(f"  ✓ Paquete TokenPulse Vinculado al Proyecto: {canonical_name}")
    print("=" * 65)
    print(f"  • Ruta:      {proj_path}")
    if git_url:
        print(f"  • Git URL:   {git_url} (Identificador Portátil)")
    print(f"  • Config:    {config_file}")
    print(f"  • Historial: {events_file}")
    print(f"\nPuedes consultar este proyecto en el Dashboard:")
    print(f"  👉 http://localhost:4120/?project={canonical_name}")
    print("=" * 65)
    return 0

def scan_projects(root_dir: str = None) -> List[Dict[str, Any]]:
    """Escanea automáticamente un directorio en busca de proyectos y los vincula."""
    if not root_dir:
        # Default: Documents / 0. Programacion or user home
        doc_prog = Path.home() / "Documents" / "0. Programacion"
        root_path = doc_prog if doc_prog.exists() else Path.home() / "Documents"
    else:
        root_path = Path(root_dir).resolve()

    if not root_path.exists():
        print(f"[Error] La ruta de escaneo no existe: {root_path}")
        return []

    print("=" * 65)
    print(f"  🔍 Escaneando Proyectos en: {root_path}")
    print("=" * 65)

    discovered = []
    db = Database()

    # Scan level 1 and 2 subdirectories
    subdirs = []
    try:
        for item in root_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                subdirs.append(item)
    except Exception as e:
        print(f"Error accediendo al directorio: {e}")
        return []

    for p in subdirs:
        has_git = (p / ".git").exists()
        has_tokenpulse = (p / ".tokenpulse").exists()
        has_code = (
            (p / "package.json").exists() or 
            (p / "pyproject.toml").exists() or 
            (p / "requirements.txt").exists() or
            (p / "Cargo.toml").exists() or
            (p / "go.mod").exists()
        )

        if has_git or has_tokenpulse or has_code:
            name = clean_project_name(None, str(p))
            git_url = get_git_remote_url(p)
            
            # Auto-init if not already initialized
            if not has_tokenpulse:
                init_project(str(p), name=name)
            else:
                db.register_project(name, str(p))

            discovered.append({
                "project_name": name,
                "project_path": str(p),
                "git_url": git_url,
                "has_git": has_git,
                "has_tokenpulse": has_tokenpulse
            })
            print(f"  ✓ Proyecto Detectado: {name:25} ({p})")

    print("\n" + "=" * 65)
    print(f"  Total Proyectos Auto-Descubiertos y Vinculados: {len(discovered)}")
    print("=" * 65)
    return discovered

def status_project(target_dir: str = "."):
    proj_path = Path(target_dir).resolve()
    canonical_name = clean_project_name(None, str(proj_path))

    # Check if there is a local config
    config_file = proj_path / ".tokenpulse" / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                canonical_name = cdata.get("project_name", canonical_name)
        except Exception:
            pass

    db = Database()
    detail = db.get_project_detail(canonical_name)
    if not detail or not detail.get("summary"):
        print(f"[Aviso] No se encontraron datos para el proyecto '{canonical_name}'.")
        print(f"Asegúrate de haber ejecutado 'tokenpulse init' o que existan sesiones en este directorio.")
        return 1

    sm = detail["summary"]
    models = detail.get("models", [])
    timeline = detail.get("timeline", [])

    print("=" * 65)
    print(f"  📊 Auditoría de Tokens: {canonical_name}")
    print("=" * 65)
    print(f"  • Ubicación:          {sm['project_path'] or str(proj_path)}")
    print(f"  • Primer Registro:    {sm.get('first_session_date') or '--'}")
    print(f"  • Último Registro:    {sm.get('last_session_date') or '--'}")
    print(f"  • Sesiones Totales:   {sm['session_count']}")
    print(f"  • Tokens de Entrada:  {sm['input_tokens']:,}")
    print(f"  • Tokens de Salida:   {sm['output_tokens']:,}")
    print(f"  • Tokens Pensamiento: {sm['reasoning_tokens']:,}")
    print(f"  • Tokens Totales:     {sm['total_tokens']:,}")
    print(f"  • Gasto Total:        ${sm['total_cost_usd']:.4f} USD\n")

    print("[Desglose por Inteligencia Artificial Utilizada]")
    if not models:
        print("  Sin modelos registrados.")
    else:
        for m in models:
            m_name = m["model_name"] or "Desconocido"
            pct = (m["total_tokens"] / sm["total_tokens"] * 100) if sm["total_tokens"] > 0 else 0
            print(f"  • {m_name:24} | {m['session_count']:3} sesiones | {m['total_tokens']:>10,} tokens ({pct:4.1f}%) | ${m['cost_usd']:.4f} USD")

    print("\n[Historial Reciente]")
    for t in timeline[-5:]:
        print(f"  • Fecha {t['date']}: {t['tokens']:,} tokens | ${t['cost_usd']:.4f} USD ({t['session_count']} procesos)")

    print("=" * 65)
    return 0

def log_event(target_dir: str = ".", description: str = "", command: str = "", model: str = "", tokens: int = 0, ide: str = "antigravity"):
    proj_path = Path(target_dir).resolve()
    canonical_name = clean_project_name(None, str(proj_path))

    config_file = proj_path / ".tokenpulse" / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                canonical_name = cdata.get("project_name", canonical_name)
        except Exception:
            pass

    pricing = PricingEngine()
    cost_usd, friendly_model = pricing.calculate_cost(model, tokens, 0) if tokens > 0 else (0.0, model)

    event_record = {
        "project_name": canonical_name,
        "event_type": "command" if command else "process",
        "description": description or "Actualización de proyecto",
        "command_text": command,
        "model_name": friendly_model,
        "tokens_used": tokens,
        "cost_usd": cost_usd,
        "source_ide": ide,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Append to local project file
    events_file = proj_path / ".tokenpulse" / "events.jsonl"
    if events_file.parent.exists():
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_record) + "\n")

    # Add to central db
    db = Database()
    db.add_project_event(
        project_name=canonical_name,
        event_type=event_record["event_type"],
        description=event_record["description"],
        command_text=command,
        model_name=friendly_model,
        tokens_used=tokens,
        cost_usd=cost_usd,
        metadata=json.dumps({"source_ide": ide})
    )

    print(f"✓ Evento registrado en '{canonical_name}' [{ide}]: {description or command} ({tokens} tokens, ${cost_usd:.4f} USD)")
    return 0

def export_project_markdown(project_name: str) -> str:
    """Genera un reporte completo en Markdown para auditar el proyecto."""
    db = Database()
    detail = db.get_project_detail(project_name)
    if not detail or not detail.get("summary"):
        return f"# Reporte: {project_name}\n\nSin datos registrados."

    sm = detail["summary"]
    models = detail.get("models", [])
    timeline = detail.get("timeline", [])

    lines = [
        f"# 📊 Auditoría de Tokens: {project_name}",
        f"**Generado el:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Ubicación:** `{sm.get('project_path', 'No especificada')}`",
        "",
        "## Resumen Acumulado (Desde el Inicio hasta Hoy)",
        f"- **Sesiones y Procesos:** {sm.get('session_count', 0)}",
        f"- **Tokens de Entrada:** {sm.get('input_tokens', 0):,}",
        f"- **Tokens de Salida:** {sm.get('output_tokens', 0):,}",
        f"- **Tokens de Pensamiento (Thinking):** {sm.get('reasoning_tokens', 0):,}",
        f"- **Tokens Totales:** {sm.get('total_tokens', 0):,}",
        f"- **Gasto Total:** ${sm.get('total_cost_usd', 0.0):.4f} USD",
        f"- **Primer Registro:** {sm.get('first_session_date', '--')}",
        f"- **Último Registro:** {sm.get('last_session_date', '--')}",
        "",
        "## Desglose por Inteligencia Artificial Utilizada",
        "| Modelo de IA | Sesiones | Tokens Entrada | Tokens Salida | Total Tokens | Gasto en USD |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for m in models:
        lines.append(f"| **{m.get('model_name')}** | {m.get('session_count')} | {m.get('input_tokens', 0):,} | {m.get('output_tokens', 0):,} | {m.get('total_tokens', 0):,} | ${m.get('cost_usd', 0.0):.4f} |")

    lines.extend([
        "",
        "## Evolución Cronológica Diaria",
        "| Fecha | Procesos | Tokens | Gasto USD |",
        "| :--- | :--- | :--- | :--- |"
    ])

    for t in timeline:
        lines.append(f"| {t.get('date')} | {t.get('session_count')} | {t.get('tokens', 0):,} | ${t.get('cost_usd', 0.0):.4f} |")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="TokenPulse CLI - Auditor de Tokens por Proyecto")
    subparsers = parser.add_subparsers(dest="action", help="Acción a realizar")

    # init
    init_parser = subparsers.add_parser("init", help="Vincular un proyecto e inicializar su seguimiento")
    init_parser.add_argument("path", nargs="?", default=".", help="Ruta de la carpeta del proyecto")
    init_parser.add_argument("--name", help="Nombre personalizado del proyecto")
    init_parser.add_argument("--budget", type=float, default=0.0, help="Presupuesto límite en USD")
    init_parser.add_argument("--tokens", type=int, default=0, help="Límite máximo de tokens")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Escanear y auto-descubrir proyectos en una carpeta")
    scan_parser.add_argument("path", nargs="?", default=None, help="Ruta raíz a escanear")

    # status
    status_parser = subparsers.add_parser("status", help="Ver auditoría y desglose por IAs de un proyecto")
    status_parser.add_argument("path", nargs="?", default=".", help="Ruta de la carpeta del proyecto")

    # log
    log_parser = subparsers.add_parser("log", help="Registrar un comando, proceso o actualización manual")
    log_parser.add_argument("description", help="Descripción del proceso realizado")
    log_parser.add_argument("--path", default=".", help="Ruta del proyecto")
    log_parser.add_argument("--cmd", default="", help="Comando ejecutado")
    log_parser.add_argument("--model", default="default", help="Modelo de IA utilizado")
    log_parser.add_argument("--ide", default="antigravity", help="Entorno o IDE (antigravity, opencode, claude, cursor, windsurf, vscode, ollama)")
    log_parser.add_argument("--tokens", type=int, default=0, help="Tokens consumidos en el proceso")

    # export
    export_parser = subparsers.add_parser("export", help="Exportar reporte de auditoría en Markdown")
    export_parser.add_argument("project", help="Nombre del proyecto a exportar")
    export_parser.add_argument("--out", default="", help="Ruta del archivo de salida")

    args = parser.parse_args()

    if args.action == "init":
        return init_project(args.path, name=args.name, budget=args.budget, token_limit=args.tokens)
    elif args.action == "scan":
        scan_projects(args.path)
        return 0
    elif args.action == "status":
        return status_project(args.path)
    elif args.action == "log":
        return log_event(args.path, description=args.description, command=args.cmd, model=args.model, tokens=args.tokens, ide=args.ide)
    elif args.action == "export":
        md = export_project_markdown(args.project)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Reporte exportado en: {args.out}")
        else:
            print(md)
        return 0
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
