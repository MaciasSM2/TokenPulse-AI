import os
from pathlib import Path
from typing import List, Dict, Any

class IDEDetector:
    """
    Detects and audits all AI IDEs and coding environments installed
    on the host operating system.
    """

    @staticmethod
    def get_known_ides() -> List[Dict[str, Any]]:
        home = Path.home()
        appdata = Path(os.environ.get("APPDATA", "")) if os.environ.get("APPDATA") else home / "AppData" / "Roaming"
        localappdata = Path(os.environ.get("LOCALAPPDATA", "")) if os.environ.get("LOCALAPPDATA") else home / "AppData" / "Local"

        ides = [
            {
                "id": "antigravity",
                "name": "Antigravity IDE",
                "vendor": "Google DeepMind",
                "badge_class": "badge-antigravity",
                "color": "#38bdf8",
                "paths": [
                    home / ".gemini" / "antigravity-ide" / "brain",
                    home / ".gemini" / "antigravity-ide"
                ],
                "description": "IDE asistido por agente con Gemini 2.5 Pro y arquitectura de subagentes.",
                "collector": "antigravity_collector"
            },
            {
                "id": "opencode",
                "name": "OpenCode Desktop",
                "vendor": "OpenCode AI",
                "badge_class": "badge-opencode",
                "color": "#c084fc",
                "paths": [
                    home / ".local" / "share" / "opencode" / "opencode.db",
                    home / ".local" / "share" / "opencode"
                ],
                "description": "Cliente open source con modelos gratuitos y de razonamiento profundo.",
                "collector": "opencode_collector"
            },
            {
                "id": "claude",
                "name": "Claude Code",
                "vendor": "Anthropic",
                "badge_class": "badge-claude",
                "color": "#d97706",
                "paths": [
                    home / ".claude",
                    home / ".claude.json"
                ],
                "description": "Herramienta CLI y agente autónomo de Anthropic para terminal y proyectos.",
                "collector": "claude_collector"
            },
            {
                "id": "ollama",
                "name": "Ollama Local AI",
                "vendor": "Ollama Community",
                "badge_class": "badge-ollama",
                "color": "#10b981",
                "paths": [
                    home / ".ollama",
                    localappdata / "Programs" / "Ollama" / "ollama.exe"
                ],
                "description": "Motor de inferencia local para ejecutar DeepSeek, Llama 3 y Qwen a coste $0.00.",
                "collector": "ollama_collector"
            },
            {
                "id": "vscode",
                "name": "VS Code AI (Cline / Copilot)",
                "vendor": "Microsoft / Cline / Roo",
                "badge_class": "badge-vscode",
                "color": "#3b82f6",
                "paths": [
                    appdata / "Code",
                    home / ".vscode"
                ],
                "description": "Entorno VS Code con extensiones de agentes AI (Cline, Roo Code, GitHub Copilot).",
                "collector": "vscode_collector"
            },
            {
                "id": "cursor",
                "name": "Cursor AI",
                "vendor": "Anysphere",
                "badge_class": "badge-cursor",
                "color": "#00f0ff",
                "paths": [
                    appdata / "Cursor",
                    home / ".cursor"
                ],
                "description": "Editor con modelos Claude 3.7 y GPT-4o integrados en el flujo de edición.",
                "collector": "cursor_collector"
            },
            {
                "id": "windsurf",
                "name": "Windsurf Editor",
                "vendor": "Codeium",
                "badge_class": "badge-windsurf",
                "color": "#06b6d4",
                "paths": [
                    appdata / "Windsurf",
                    home / ".windsurf"
                ],
                "description": "IDE enfocado en flujos de Cascade de Codeium y contexto multi-archivo.",
                "collector": "windsurf_collector"
            },
            {
                "id": "continue",
                "name": "Continue.dev",
                "vendor": "Continue Open Source",
                "badge_class": "badge-continue",
                "color": "#ec4899",
                "paths": [
                    home / ".continue",
                    home / ".continue" / "sessions"
                ],
                "description": "Extensión open source para conectar cualquier LLM comercial o local a VS Code o JetBrains.",
                "collector": "continue_collector"
            },
            {
                "id": "aider",
                "name": "Aider Pair Programming",
                "vendor": "Paul Gauthier / Aider",
                "badge_class": "badge-aider",
                "color": "#84cc16",
                "paths": [
                    home / ".aider.conf.yml"
                ],
                "description": "Herramienta CLI de pair programming que commitea automáticamente en git.",
                "collector": "aider_collector"
            }
        ]

        result = []
        for ide in ides:
            detected_path = None
            is_detected = False
            for p in ide["paths"]:
                if p.exists():
                    detected_path = str(p)
                    is_detected = True
                    break

            result.append({
                "id": ide["id"],
                "name": ide["name"],
                "vendor": ide["vendor"],
                "badge_class": ide["badge_class"],
                "color": ide["color"],
                "detected": is_detected,
                "detected_path": detected_path,
                "status": "active" if is_detected else "not_installed",
                "status_label": "Conectado / Detectado" if is_detected else "Listo para vincular",
                "description": ide["description"]
            })

        return result
