import json
from pathlib import Path
from backend.database import Database
from backend.pricing import PricingEngine

class OllamaCollector:
    """
    Collector for Ollama local AI runtime.
    Scans installed models in ~/.ollama/models and records local execution tracking at $0.00.
    """
    def __init__(self, db: Database, pricing: PricingEngine):
        self.db = db
        self.pricing = pricing
        self.home = Path.home()
        self.ollama_dir = self.home / ".ollama"
        self.models_manifest = self.ollama_dir / "models" / "manifests"

    def sync(self) -> int:
        if not self.ollama_dir.exists():
            return 0

        synced = 0
        # If models are installed, register local audit session
        if self.models_manifest.exists():
            for m_path in self.models_manifest.rglob("*"):
                if m_path.is_file():
                    model_tag = m_path.name
                    model_id = f"ollama-{model_tag}"
                    record = {
                        "id": f"ollama_{model_tag}",
                        "source_ide": "ollama",
                        "session_id": f"ollama_{model_tag}",
                        "title": f"Ollama Local Model ({model_tag})",
                        "project_name": "General",
                        "project_path": "",
                        "model_id": model_id,
                        "model_name": f"Ollama {model_tag} (Local)",
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "reasoning_tokens": 0,
                        "cache_read_tokens": 0,
                        "cache_write_tokens": 0,
                        "cost_usd": 0.0,
                        "start_time": "",
                        "end_time": "",
                        "step_count": 1,
                        "has_caveman": 0,
                        "has_graphify": 0,
                        "raw_metadata": json.dumps({"source": "ollama", "manifest": str(m_path)})
                    }
                    self.db.upsert_session(record)
                    synced += 1

        return synced
