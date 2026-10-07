"""
TokenPulse AI - Python SDK de Medición y Auditoría de Tokens para Proyectos Externos.
Permite instrumentar código Python, pipelines de IA, bots o juegos (como Ren'Py) con 2 líneas de código.
Falla de forma silenciosa y segura para garantizar que nunca interrumpa el flujo del proyecto anfitrión.
"""

import os
import sys
import json
import time
import functools
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable

class TokenTracker:
    """
    Rastreador de tokens liviano y portátil para proyectos de software.
    Guarda eventos localmente en .tokenpulse/events.jsonl y en la base central si está disponible.
    """

    def __init__(self, project_name: Optional[str] = None, project_path: Optional[str] = None):
        self.project_path = Path(project_path).resolve() if project_path else Path.cwd().resolve()
        self.project_name = project_name or self._detect_project_name()
        self.tokenpulse_dir = self.project_path / ".tokenpulse"
        self._ensure_storage()

    def _detect_project_name(self) -> str:
        """Intenta leer el nombre desde .tokenpulse/config.json o el nombre de la carpeta raíz."""
        config_file = self.project_path / ".tokenpulse" / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("project_name"):
                        return cfg["project_name"]
            except Exception:
                pass
        return self.project_path.name

    def _ensure_storage(self):
        """Crea el directorio local .tokenpulse si no existe."""
        try:
            self.tokenpulse_dir.mkdir(parents=True, exist_ok=True)
            config_file = self.tokenpulse_dir / "config.json"
            if not config_file.exists():
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "project_name": self.project_name,
                        "project_path": str(self.project_path),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }, f, indent=2)
        except Exception:
            pass

    def log(
        self,
        model: str = "default",
        input_tokens: int = 0,
        output_tokens: int = 0,
        reasoning_tokens: int = 0,
        ide: str = "python-sdk",
        command: str = "",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registra una invocación a un LLM o consumo de tokens.
        
        Args:
            model: Identificador del modelo (ej: 'claude-3-7-sonnet', 'gpt-4o', 'gemini-2.5-pro')
            input_tokens: Tokens de entrada / prompt
            output_tokens: Tokens de salida / respuesta
            reasoning_tokens: Tokens de pensamiento / razonamiento (ej: o1, o3-mini, deepseek-r1)
            ide: Nombre del entorno (por defecto 'python-sdk')
            command: Función o script ejecutado (opcional)
            description: Descripción legible de la tarea realizada
            metadata: Diccionario opcional con metadatos extra
        
        Returns:
            Dict con los datos del evento registrado.
        """
        total_tokens = input_tokens + output_tokens + reasoning_tokens
        now_iso = datetime.now(timezone.utc).isoformat()

        event_data = {
            "timestamp": now_iso,
            "project_name": self.project_name,
            "source_ide": ide,
            "model_name": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "total_tokens": total_tokens,
            "command": command,
            "description": description or f"Llamada LLM vía TokenTracker ({model})",
            "metadata": metadata or {}
        }

        # 1. Guardar localmente en el proyecto (.tokenpulse/events.jsonl)
        try:
            events_file = self.tokenpulse_dir / "events.jsonl"
            with open(events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
        except Exception:
            pass

        # 2. Registrar en la base central si backend está disponible en el entorno
        try:
            from backend.database import Database
            db = Database()
            db.register_project(self.project_name, str(self.project_path))
            db.insert_session({
                "session_id": f"sdk_{int(time.time()*1000)}_{os.getpid()}",
                "project_name": self.project_name,
                "project_path": str(self.project_path),
                "source_ide": ide,
                "model_name": model,
                "model_id": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "reasoning_tokens": reasoning_tokens,
                "total_tokens": total_tokens,
                "start_time": now_iso,
                "title": event_data["description"]
            })
        except Exception:
            pass

        return event_data

    def track(self, model: str = "default", ide: str = "python-sdk", description: str = ""):
        """
        Decorador para envolver funciones que llaman a un LLM.
        Si la función retorna un objeto con atributo 'usage' (como OpenAI o Anthropic),
        extrae los tokens automáticamente.
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                res = func(*args, **kwargs)
                in_tok = 0
                out_tok = 0
                reason_tok = 0

                # Detección automática en respuestas de OpenAI / Anthropic
                if hasattr(res, "usage") and res.usage:
                    u = res.usage
                    in_tok = getattr(u, "prompt_tokens", getattr(u, "input_tokens", 0))
                    out_tok = getattr(u, "completion_tokens", getattr(u, "output_tokens", 0))
                    reason_details = getattr(u, "completion_tokens_details", None)
                    if reason_details:
                        reason_tok = getattr(reason_details, "reasoning_tokens", 0)
                elif isinstance(res, dict) and "usage" in res:
                    u = res["usage"]
                    in_tok = u.get("prompt_tokens", u.get("input_tokens", 0))
                    out_tok = u.get("completion_tokens", u.get("output_tokens", 0))

                desc = description or f"Ejecución de {func.__name__}"
                self.log(
                    model=model,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    reasoning_tokens=reason_tok,
                    ide=ide,
                    command=func.__name__,
                    description=desc
                )
                return res
            return wrapper
        return decorator


# Instancia singleton rápida para uso inmediato
_default_tracker: Optional[TokenTracker] = None

def get_tracker(project_name: Optional[str] = None) -> TokenTracker:
    """Retorna una instancia activa del rastreador."""
    global _default_tracker
    if _default_tracker is None or (_default_tracker and project_name and _default_tracker.project_name != project_name):
        _default_tracker = TokenTracker(project_name=project_name)
    return _default_tracker

def track_usage(
    model: str = "default",
    input_tokens: int = 0,
    output_tokens: int = 0,
    project_name: Optional[str] = None,
    description: str = "",
    command: str = ""
) -> Dict[str, Any]:
    """Función de una sola línea para registrar consumo desde cualquier script."""
    tracker = get_tracker(project_name)
    return tracker.log(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        description=description,
        command=command
    )
