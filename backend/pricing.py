import json
import re
from typing import Dict, Any, Tuple
from backend.config import PRICING_FILE_PATH

class PricingEngine:
    def __init__(self, config_path=PRICING_FILE_PATH):
        self.config_path = config_path
        self.models: Dict[str, Any] = {}
        self.load_pricing()

    def load_pricing(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.models = data.get("models", {})
            except Exception as e:
                print(f"[PricingEngine] Error loading pricing config: {e}")
                self.models = {}

    def normalize_model_name(self, raw_model: str) -> str:
        if not raw_model:
            return "default"
        
        m = raw_model.lower().strip()

        # Handle OpenCode JSON model strings
        if m.startswith("{") and "id" in m:
            try:
                parsed = json.loads(raw_model)
                m = parsed.get("id", "").lower()
            except Exception:
                pass

        if "free" in m or "pickle" in m:
            if "deepseek-v4-flash-free" in m:
                return "deepseek-v4-flash-free"
            if "nemotron" in m:
                return "nemotron-3-ultra-free"
            if "mimo" in m:
                return "mimo-v2.5-free"
            if "pickle" in m:
                return "big-pickle"
            return "deepseek-v4-flash-free"

        if "gemini" in m:
            if "3.8" in m and "flash" in m:
                return "gemini-3.8-flash"
            if "2.5" in m and "pro" in m:
                return "gemini-2.5-pro"
            if "2.0" in m and "flash" in m:
                return "gemini-2.0-flash"
            if "flash" in m:
                return "gemini-flash"
            if "pro" in m:
                return "gemini-2.5-pro"
            return "gemini-flash"

        if "claude" in m:
            if "3-7" in m or "3.7" in m:
                return "claude-3-7-sonnet"
            if "haiku" in m:
                return "claude-3-5-haiku"
            return "claude-3-5-sonnet"

        if "gpt-4o-mini" in m:
            return "gpt-4o-mini"
        if "gpt-4o" in m:
            return "gpt-4o"

        if "deepseek" in m:
            if "reasoner" in m or "r1" in m:
                return "deepseek-reasoner"
            return "deepseek-chat"

        return "default"

    def calculate_cost(self, raw_model: str, input_tokens: int, output_tokens: int) -> Tuple[float, str]:
        key = self.normalize_model_name(raw_model)
        rate = self.models.get(key, self.models.get("default", {
            "name": "Default",
            "input_per_million": 0.50,
            "output_per_million": 2.00
        }))

        in_rate = rate.get("input_per_million", 0.50) / 1_000_000.0
        out_rate = rate.get("output_per_million", 2.00) / 1_000_000.0

        cost = (input_tokens * in_rate) + (output_tokens * out_rate)
        friendly_name = rate.get("name", key)
        return round(cost, 6), friendly_name
