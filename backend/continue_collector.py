import json
from pathlib import Path
from typing import Dict, Any
from backend.database import Database
from backend.pricing import PricingEngine

class ContinueCollector:
    """
    Collector for Continue.dev sessions.
    Reads ~/.continue/sessions/ and parses LLM interactions.
    """
    def __init__(self, db: Database, pricing: PricingEngine):
        self.db = db
        self.pricing = pricing
        self.home = Path.home()
        self.sessions_dir = self.home / ".continue" / "sessions"

    def sync(self) -> int:
        if not self.sessions_dir.exists():
            return 0

        synced_count = 0
        for item in self.sessions_dir.glob("*.json"):
            try:
                with open(item, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if self._process_session(item.stem, data):
                    synced_count += 1
            except Exception as e:
                print(f"[ContinueCollector] Error reading {item}: {e}")

        return synced_count

    def _process_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        title = data.get("title", f"Continue Session {session_id[:8]}")
        workspace_dir = data.get("workspaceDirectory", "")
        history = data.get("history", [])

        input_tokens = 0
        output_tokens = 0
        model_name = "default"
        start_time = data.get("dateCreated", "")

        for step in history:
            m_info = step.get("modelTitle") or step.get("model") or ""
            if m_info:
                model_name = m_info
            # Approximate or extract prompt/completion tokens
            p_text = step.get("prompt", "")
            c_text = step.get("completion", "")
            # If explicit tokens
            if "promptTokens" in step:
                input_tokens += step.get("promptTokens", 0)
                output_tokens += step.get("completionTokens", 0)
            else:
                # Est: 1 token ~= 4 chars
                input_tokens += max(10, len(p_text) // 4)
                output_tokens += max(10, len(c_text) // 4)

        cost_usd, friendly_model = self.pricing.calculate_cost(model_name, input_tokens, output_tokens)

        record = {
            "id": f"continue_{session_id}",
            "source_ide": "continue",
            "session_id": session_id,
            "title": title,
            "project_name": Path(workspace_dir).name if workspace_dir else "General",
            "project_path": workspace_dir,
            "model_id": model_name,
            "model_name": friendly_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "cost_usd": cost_usd,
            "start_time": start_time,
            "end_time": start_time,
            "step_count": len(history),
            "has_caveman": 1 if "caveman" in str(data).lower() else 0,
            "has_graphify": 1 if "graphify" in str(data).lower() else 0,
            "raw_metadata": json.dumps({"source": "continue_dev", "session_id": session_id})
        }

        self.db.upsert_session(record)
        return True
