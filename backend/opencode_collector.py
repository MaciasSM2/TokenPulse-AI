import sqlite3
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from backend.config import OPENCODE_DB_PATH
from backend.database import Database
from backend.pricing import PricingEngine

class OpenCodeCollector:
    def __init__(self, db: Database, pricing: PricingEngine, source_db_path: Path = OPENCODE_DB_PATH):
        self.db = db
        self.pricing = pricing
        self.source_db_path = source_db_path

    def is_available(self) -> bool:
        return self.source_db_path.exists()

    def sync(self) -> int:
        if not self.is_available():
            print(f"[OpenCodeCollector] Base de datos no encontrada en {self.source_db_path}")
            return 0

        # Read directly using SQLite in read-only URI mode to avoid locking
        uri = f"file:{self.source_db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT 
                    id, project_id, directory, title, agent, model,
                    cost, tokens_input, tokens_output, tokens_reasoning,
                    tokens_cache_read, tokens_cache_write,
                    time_created, time_updated, metadata
                FROM session
            """)
            sessions = cur.fetchall()
        except Exception as e:
            print(f"[OpenCodeCollector] Error al consultar sesiones: {e}")
            conn.close()
            return 0

        synced_count = 0

        for row in sessions:
            s_id = row["id"]
            directory = row["directory"] or ""
            project_name = Path(directory).name if directory else "OpenCode Workspace"
            title = row["title"] or f"Sesión {s_id[:8]}"
            raw_model = row["model"] or "default"
            
            in_tok = row["tokens_input"] or 0
            out_tok = row["tokens_output"] or 0
            reason_tok = row["tokens_reasoning"] or 0
            cache_read = row["tokens_cache_read"] or 0
            cache_write = row["tokens_cache_write"] or 0
            
            calc_cost, model_name = self.pricing.calculate_cost(raw_model, in_tok, out_tok)
            # If native cost exists and is > 0, prefer native cost, else use calculated
            cost_usd = row["cost"] if (row["cost"] is not None and row["cost"] > 0) else calc_cost

            # Timestamps
            created_ms = row["time_created"]
            updated_ms = row["time_updated"]
            start_time = datetime.fromtimestamp(created_ms / 1000.0, tz=timezone.utc).isoformat() if created_ms else ""
            end_time = datetime.fromtimestamp(updated_ms / 1000.0, tz=timezone.utc).isoformat() if updated_ms else ""

            # Check optimizations
            agent_str = str(row["agent"] or "").lower()
            meta_str = str(row["metadata"] or "").lower()
            title_lower = title.lower()

            has_caveman = 1 if ("cave" in agent_str or "caveman" in meta_str or "caveman" in title_lower) else 0
            has_graphify = 1 if ("graphify" in meta_str or "graphify" in title_lower) else 0

            record = {
                "id": f"opencode:{s_id}",
                "source_ide": "opencode",
                "session_id": s_id,
                "title": title,
                "project_name": project_name,
                "project_path": directory,
                "model_id": str(raw_model),
                "model_name": model_name,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "reasoning_tokens": reason_tok,
                "cache_read_tokens": cache_read,
                "cache_write_tokens": cache_write,
                "cost_usd": cost_usd,
                "start_time": start_time,
                "end_time": end_time,
                "step_count": 0,
                "has_caveman": has_caveman,
                "has_graphify": has_graphify,
                "raw_metadata": row["metadata"] or ""
            }

            self.db.upsert_session(record)
            synced_count += 1

        conn.close()
        print(f"[OpenCodeCollector] Sincronizadas con éxito {synced_count} sesiones de OpenCode.")
        return synced_count
