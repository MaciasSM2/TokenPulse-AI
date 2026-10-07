import json
import os
from pathlib import Path
from typing import Dict, Any
from backend.database import Database
from backend.pricing import PricingEngine

class ClaudeCodeCollector:
    """
    Collector for Claude Code CLI and Anthropic agent sessions.
    Reads ~/.claude/sessions and project-level Claude traces.
    """
    def __init__(self, db: Database, pricing: PricingEngine):
        self.db = db
        self.pricing = pricing
        self.home = Path.home()
        self.claude_dir = self.home / ".claude"
        self.sessions_dir = self.claude_dir / "sessions"

    def sync(self) -> int:
        synced_count = 0
        if not self.claude_dir.exists():
            return 0

        # 1. Scan global sessions dir
        if self.sessions_dir.exists():
            for item in self.sessions_dir.glob("*.json"):
                try:
                    with open(item, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if self._process_session(item.stem, data):
                        synced_count += 1
                except Exception as e:
                    print(f"[ClaudeCollector] Error parsing session {item}: {e}")

        # 2. Check registered projects for .claude session history
        projects = self.db.get_projects_list()
        for p in projects:
            p_path = p.get("project_path")
            if not p_path or not Path(p_path).exists():
                continue
            p_claude = Path(p_path) / ".claude"
            if p_claude.exists() and p_claude.is_dir():
                for s_file in p_claude.glob("**/*.json"):
                    try:
                        with open(s_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if self._process_session(s_file.stem, data, project_name=p.get("project_name"), project_path=p_path):
                            synced_count += 1
                    except Exception as e:
                        print(f"[ClaudeCollector] Error parsing project session {s_file}: {e}")

        return synced_count

    def _process_session(self, session_id: str, data: Dict[str, Any], project_name: str = "General", project_path: str = "") -> bool:
        if not isinstance(data, dict):
            return False

        # Extract tokens and model
        model_raw = data.get("model", "claude-3-7-sonnet")
        input_tokens = data.get("input_tokens", data.get("prompt_tokens", 0))
        output_tokens = data.get("output_tokens", data.get("completion_tokens", 0))
        reasoning_tokens = data.get("reasoning_tokens", data.get("thinking_tokens", 0))
        title = data.get("title", data.get("summary", f"Claude Code Session {session_id[:8]}"))
        start_time = data.get("created_at", data.get("timestamp", ""))

        if input_tokens == 0 and output_tokens == 0:
            # Check messages array if available
            messages = data.get("messages", [])
            for msg in messages:
                usage = msg.get("usage", {})
                input_tokens += usage.get("input_tokens", 0)
                output_tokens += usage.get("output_tokens", 0)
                reasoning_tokens += usage.get("thinking_tokens", 0)

        cost_usd, friendly_model = self.pricing.calculate_cost(model_raw, input_tokens, output_tokens)

        record = {
            "id": f"claude_{session_id}",
            "source_ide": "claude",
            "session_id": session_id,
            "title": title,
            "project_name": project_name,
            "project_path": project_path,
            "model_id": model_raw,
            "model_name": friendly_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "cost_usd": cost_usd,
            "start_time": start_time,
            "end_time": start_time,
            "step_count": len(data.get("messages", [])),
            "has_caveman": 1 if "caveman" in str(data).lower() else 0,
            "has_graphify": 1 if "graphify" in str(data).lower() else 0,
            "raw_metadata": json.dumps({"source": "claude_code", "session_id": session_id})
        }

        self.db.upsert_session(record)
        return True
