import os
import json
from pathlib import Path
from backend.database import Database
from backend.pricing import PricingEngine

class VSCodeAICollector:
    """
    Collector for VS Code AI extensions (Cline, Roo Code, GitHub Copilot).
    Scans AppData/Roaming/Code/User/globalStorage for extension chat task histories.
    """
    def __init__(self, db: Database, pricing: PricingEngine):
        self.db = db
        self.pricing = pricing
        self.home = Path.home()
        self.appdata = Path(os.environ.get("APPDATA", "")) if os.environ.get("APPDATA") else self.home / "AppData" / "Roaming"
        self.global_storage = self.appdata / "Code" / "User" / "globalStorage"

    def sync(self) -> int:
        if not self.global_storage.exists():
            return 0

        synced_count = 0
        # Check for Cline (saoudrizwan.claude-dev) and Roo Code (rooveterinaryinc.roo-cline)
        target_exts = [
            ("saoudrizwan.claude-dev", "Cline"),
            ("rooveterinaryinc.roo-cline", "Roo Code")
        ]

        for ext_folder, label in target_exts:
            tasks_dir = self.global_storage / ext_folder / "tasks"
            if tasks_dir.exists():
                for t_dir in tasks_dir.iterdir():
                    if not t_dir.is_dir():
                        continue
                    api_conv = t_dir / "api_conversation_history.json"
                    ui_msg = t_dir / "ui_messages.json"
                    target_file = api_conv if api_conv.exists() else ui_msg
                    if target_file and target_file.exists():
                        try:
                            with open(target_file, "r", encoding="utf-8") as f:
                                msgs = json.load(f)
                            if self._process_task(t_dir.name, msgs, label):
                                synced_count += 1
                        except Exception as e:
                            print(f"[VSCodeAICollector] Error reading task {t_dir}: {e}")

        return synced_count

    def _process_task(self, task_id: str, msgs: list, label: str) -> bool:
        if not msgs or not isinstance(msgs, list):
            return False

        in_tokens = 0
        out_tokens = 0
        model_name = "claude-3-5-sonnet"

        for m in msgs:
            if isinstance(m, dict):
                # Check for usage object
                usage = m.get("usage", {})
                if usage:
                    in_tokens += usage.get("input_tokens", 0)
                    out_tokens += usage.get("output_tokens", 0)
                if m.get("model"):
                    model_name = m.get("model")

        if in_tokens == 0 and out_tokens == 0:
            char_count = sum(len(str(m)) for m in msgs)
            tokens = max(50, char_count // 4)
            in_tokens = int(tokens * 0.7)
            out_tokens = int(tokens * 0.3)

        cost, friendly_model = self.pricing.calculate_cost(model_name, in_tokens, out_tokens)

        record = {
            "id": f"vscode_{task_id}",
            "source_ide": "vscode",
            "session_id": task_id,
            "title": f"{label} Task {task_id[:8]}",
            "project_name": "General",
            "project_path": "",
            "model_id": model_name,
            "model_name": friendly_model,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "reasoning_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "cost_usd": cost,
            "start_time": "",
            "end_time": "",
            "step_count": len(msgs),
            "has_caveman": 1 if "caveman" in str(msgs).lower() else 0,
            "has_graphify": 1 if "graphify" in str(msgs).lower() else 0,
            "raw_metadata": json.dumps({"source": "vscode", "ext": label, "task_id": task_id})
        }
        self.db.upsert_session(record)
        return True
