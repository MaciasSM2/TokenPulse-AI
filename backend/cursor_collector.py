import os
import json
import sqlite3
from pathlib import Path
from backend.database import Database
from backend.pricing import PricingEngine

class CursorWindsurfCollector:
    """
    Collector for Cursor and Windsurf editors.
    Scans AppData/Roaming/Cursor and AppData/Roaming/Windsurf workspaceStorage databases.
    """
    def __init__(self, db: Database, pricing: PricingEngine):
        self.db = db
        self.pricing = pricing
        self.home = Path.home()
        self.appdata = Path(os.environ.get("APPDATA", "")) if os.environ.get("APPDATA") else self.home / "AppData" / "Roaming"

    def sync(self) -> int:
        count = 0
        count += self._sync_ide("cursor", self.appdata / "Cursor" / "User" / "workspaceStorage")
        count += self._sync_ide("windsurf", self.appdata / "Windsurf" / "User" / "workspaceStorage")
        return count

    def _sync_ide(self, ide_name: str, ws_storage: Path) -> int:
        if not ws_storage.exists():
            return 0

        synced = 0
        for ws_dir in ws_storage.iterdir():
            if not ws_dir.is_dir():
                continue
            db_file = ws_dir / "state.vscdb"
            if not db_file.exists():
                continue

            try:
                # Query state.vscdb
                conn = sqlite3.connect(str(db_file))
                cur = conn.cursor()
                cur.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%composer%' LIMIT 10")
                rows = cur.fetchall()
                conn.close()

                if rows:
                    session_id = f"{ide_name}_{ws_dir.name[:8]}"
                    # Check workspace.json if present
                    ws_json = ws_dir / "workspace.json"
                    proj_name = "General"
                    proj_path = ""
                    if ws_json.exists():
                        try:
                            with open(ws_json, "r", encoding="utf-8") as f:
                                w_data = json.load(f)
                                folder = w_data.get("folder", "")
                                if folder:
                                    proj_path = folder.replace("file:///", "").replace("%20", " ")
                                    proj_name = Path(proj_path).name
                        except Exception:
                            pass

                    total_chars = sum(len(str(r[1])) for r in rows)
                    tokens = max(100, total_chars // 4)
                    in_tokens = int(tokens * 0.7)
                    out_tokens = int(tokens * 0.3)
                    default_model = "claude-3-5-sonnet" if ide_name == "cursor" else "codestral"
                    cost, friendly_model = self.pricing.calculate_cost(default_model, in_tokens, out_tokens)

                    record = {
                        "id": f"{ide_name}_{ws_dir.name}",
                        "source_ide": ide_name,
                        "session_id": session_id,
                        "title": f"{ide_name.capitalize()} Workspace Session",
                        "project_name": proj_name,
                        "project_path": proj_path,
                        "model_id": default_model,
                        "model_name": friendly_model,
                        "input_tokens": in_tokens,
                        "output_tokens": out_tokens,
                        "reasoning_tokens": 0,
                        "cache_read_tokens": 0,
                        "cache_write_tokens": 0,
                        "cost_usd": cost,
                        "start_time": "",
                        "end_time": "",
                        "step_count": len(rows),
                        "has_caveman": 0,
                        "has_graphify": 0,
                        "raw_metadata": json.dumps({"source": ide_name, "ws_id": ws_dir.name})
                    }
                    self.db.upsert_session(record)
                    synced += 1
            except Exception as e:
                # ignore transient sqlite lock errors
                pass

        return synced
