import os
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import tiktoken

from backend.config import ANTIGRAVITY_BRAIN_PATH, ANTIGRAVITY_CONVERSATIONS_PATH
from backend.database import Database, clean_project_name
from backend.pricing import PricingEngine

class AntigravityCollector:
    def __init__(self, db: Database, pricing: PricingEngine, brain_path: Path = ANTIGRAVITY_BRAIN_PATH):
        self.db = db
        self.pricing = pricing
        self.brain_path = brain_path
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def is_available(self) -> bool:
        return self.brain_path.exists()

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text, disallowed_special=()))
            except Exception:
                pass
        # Fallback ratio: ~3.8 chars per token
        return max(1, int(len(text) / 3.8))

    def sync(self) -> int:
        if not self.is_available():
            print(f"[AntigravityCollector] Directorio brain no encontrado en {self.brain_path}")
            return 0

        # Find all transcript files
        transcript_patterns = [
            str(self.brain_path / "*" / ".system_generated" / "logs" / "transcript_full.jsonl"),
            str(self.brain_path / "*" / ".system_generated" / "logs" / "transcript.jsonl")
        ]
        
        seen_convs = set()
        files_to_process = []
        for pat in transcript_patterns:
            for filepath in glob.glob(pat):
                conv_id = Path(filepath).parent.parent.parent.name
                if conv_id not in seen_convs:
                    seen_convs.add(conv_id)
                    files_to_process.append((conv_id, Path(filepath)))

        synced_count = 0

        for conv_id, log_file in files_to_process:
            try:
                stat = log_file.stat()
                sync_key = f"antigravity_mtime:{conv_id}"
                last_mtime = self.db.get_sync_state(sync_key)
                current_mtime = str(stat.st_mtime)

                # Skip if already parsed and not modified
                if last_mtime == current_mtime:
                    continue

                record = self.parse_transcript(conv_id, log_file)
                if record:
                    self.db.upsert_session(record)
                    self.db.set_sync_state(sync_key, current_mtime)
                    synced_count += 1
            except Exception as e:
                print(f"[AntigravityCollector] Error procesando conversación {conv_id}: {e}")

        print(f"[AntigravityCollector] Sincronizadas {synced_count} conversaciones de Antigravity.")
        return synced_count

    def parse_transcript(self, conv_id: str, log_file: Path) -> Optional[Dict[str, Any]]:
        steps = 0
        in_tokens = 0
        out_tokens = 0
        reasoning_tokens = 0
        detected_model = "gemini-2.5-pro"  # Default Antigravity model
        first_time = ""
        last_time = ""
        project_path = ""
        first_prompt_snippet = ""
        has_caveman = 0
        has_graphify = 0

        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                except Exception:
                    continue

                steps += 1
                created_at = data.get("created_at") or ""
                if not first_time and created_at:
                    first_time = created_at
                if created_at:
                    last_time = created_at

                stype = data.get("type", "")
                source = data.get("source", "")
                content = data.get("content", "") or ""

                # Detect model settings change
                if "Model Selection" in str(content):
                    if "Gemini 3.8 Flash" in content:
                        detected_model = "gemini-3.8-flash"
                    elif "Gemini 2.5 Pro" in content:
                        detected_model = "gemini-2.5-pro"
                    elif "Gemini 2.0 Flash" in content:
                        detected_model = "gemini-2.0-flash"

                # Check optimizations in prompts or tools
                content_lower = content.lower() if isinstance(content, str) else ""
                if "graphify" in content_lower:
                    has_graphify = 1
                if "caveman" in content_lower:
                    has_caveman = 1

                # Check if workspace path can be found in content
                if not project_path and isinstance(content, str):
                    if "0. Programacion" in content or "0. programacion" in content:
                        import re
                        m = re.search(r'([a-zA-Z]:[\\/][^"\'\n\r]+0\.\s*Programacion[\\/][^"\'\\/\n\r]+)', content, re.IGNORECASE)
                        if m:
                            project_path = m.group(1).strip()

                # Input: User input, instructions, or tool execution returns
                if source in ("USER_EXPLICIT", "SYSTEM") or stype in (
                    "RUN_COMMAND", "VIEW_FILE", "LIST_DIRECTORY", "SEARCH_WEB", "CALL_MCP_TOOL"
                ):
                    toks = self.estimate_tokens(content) if isinstance(content, str) else 0
                    in_tokens += toks

                    if source == "USER_EXPLICIT" and not first_prompt_snippet:
                        first_prompt_snippet = content.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()[:80]

                # Output: Model plan, thinking, and tool call payload
                elif source == "MODEL" and stype == "PLANNER_RESPONSE":
                    thinking = data.get("thinking", "") or ""
                    if thinking:
                        th_toks = self.estimate_tokens(thinking)
                        reasoning_tokens += th_toks
                        out_tokens += th_toks

                    tool_calls = data.get("tool_calls", [])
                    if tool_calls:
                        tc_str = json.dumps(tool_calls)
                        out_tokens += self.estimate_tokens(tc_str)

                        # Extract workspace directory from tool arguments
                        if not project_path:
                            for tc in tool_calls:
                                args = tc.get("args", {})
                                if isinstance(args, dict):
                                    for key in ("Cwd", "DirectoryPath", "SearchPath", "TargetFile", "AbsolutePath"):
                                        val = args.get(key)
                                        if val and isinstance(val, str) and len(val) > 3:
                                            project_path = val.strip('\"\'')
                                            break
                                if project_path:
                                    break

        cost_usd, friendly_model_name = self.pricing.calculate_cost(detected_model, in_tokens, out_tokens)

        title = first_prompt_snippet or f"Conversación {conv_id[:8]}"
        title = title.replace("\n", " ").strip()
        project_name = clean_project_name(None, project_path)

        return {
            "id": f"antigravity:{conv_id}",
            "source_ide": "antigravity",
            "session_id": conv_id,
            "title": title[:100],
            "project_name": project_name,
            "project_path": project_path,
            "model_id": detected_model,
            "model_name": friendly_model_name,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "reasoning_tokens": reasoning_tokens,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "cost_usd": cost_usd,
            "start_time": first_time,
            "end_time": last_time,
            "step_count": steps,
            "has_caveman": has_caveman,
            "has_graphify": has_graphify,
            "raw_metadata": json.dumps({"source": "brain_transcripts"})
        }
