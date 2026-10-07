import re
import json
from pathlib import Path
from backend.database import Database
from backend.pricing import PricingEngine

class AiderCollector:
    """
    Collector for Aider pair-programming sessions.
    Scans project folders for .aider.chat.history.md files.
    """
    def __init__(self, db: Database, pricing: PricingEngine):
        self.db = db
        self.pricing = pricing

    def sync(self) -> int:
        synced_count = 0
        projects = self.db.get_projects_list()
        
        for p in projects:
            p_path = p.get("project_path")
            if not p_path or not Path(p_path).exists():
                continue

            aider_file = Path(p_path) / ".aider.chat.history.md"
            if aider_file.exists():
                try:
                    if self._process_aider_file(aider_file, p.get("project_name", "General"), p_path):
                        synced_count += 1
                except Exception as e:
                    print(f"[AiderCollector] Error reading {aider_file}: {e}")

        return synced_count

    def _process_aider_file(self, file_path: Path, project_name: str, project_path: str) -> bool:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not content:
            return False

        # Find models used
        model_match = re.search(r'model:\s*([a-zA-Z0-9_\-\.]+)', content, re.IGNORECASE)
        model_name = model_match.group(1) if model_match else "claude-3-5-sonnet"

        # Approximate tokens based on conversation size (1 token ~= 4 chars)
        total_chars = len(content)
        total_tokens = total_chars // 4
        in_tokens = int(total_tokens * 0.7)
        out_tokens = int(total_tokens * 0.3)

        cost_usd, friendly_model = self.pricing.calculate_cost(model_name, in_tokens, out_tokens)

        record = {
            "id": f"aider_{project_name.lower().replace(' ', '_')}",
            "source_ide": "aider",
            "session_id": f"aider_{project_name}",
            "title": f"Aider Chat History ({project_name})",
            "project_name": project_name,
            "project_path": project_path,
            "model_id": model_name,
            "model_name": friendly_model,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "reasoning_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "cost_usd": cost_usd,
            "start_time": "",
            "end_time": "",
            "step_count": content.count("#### "),
            "has_caveman": 1 if "caveman" in content.lower() else 0,
            "has_graphify": 1 if "graphify" in content.lower() else 0,
            "raw_metadata": json.dumps({"source": "aider", "file": str(file_path)})
        }

        self.db.upsert_session(record)
        return True
