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

        # 1. Free tier models & OpenCode proxies
        if "free" in m or "pickle" in m:
            if "deepseek-v4-flash-free" in m or "v4-flash" in m:
                return "deepseek-v4-flash-free"
            if "nemotron" in m:
                return "nemotron-3-ultra-free"
            if "mimo" in m:
                return "mimo-v2.5-free"
            if "pickle" in m:
                return "big-pickle"
            if "gemini" in m:
                return "gemini-free"
            return "deepseek-v4-flash-free"

        # 2. Ollama / Local Models
        if "ollama" in m or "local" in m:
            if "deepseek" in m or "r1" in m:
                return "ollama-deepseek-r1"
            if "qwen" in m or "coder" in m:
                return "ollama-qwen-coder"
            if "llama" in m:
                return "ollama-llama3"
            return "ollama-local"

        # 3. Google Gemini
        if "gemini" in m:
            if "3.8" in m and "flash" in m:
                return "gemini-3.8-flash"
            if "2.5" in m and "pro" in m:
                return "gemini-2.5-pro"
            if "2.0" in m and ("thinking" in m or "think" in m):
                return "gemini-2.0-flash-thinking"
            if "2.0" in m and "flash" in m:
                return "gemini-2.0-flash"
            if "1.5" in m and "pro" in m:
                return "gemini-1.5-pro"
            if "1.5" in m and "flash" in m:
                return "gemini-1.5-flash"
            if "flash" in m:
                return "gemini-flash"
            if "pro" in m:
                return "gemini-2.5-pro"
            return "gemini-flash"

        # 4. Anthropic Claude
        if "claude" in m:
            if "3-7" in m or "3.7" in m:
                return "claude-3-7-sonnet"
            if "haiku" in m:
                return "claude-3-5-haiku"
            if "opus" in m:
                return "claude-3-opus"
            if "3-sonnet" in m or "3.0-sonnet" in m:
                return "claude-3-sonnet"
            return "claude-3-5-sonnet"

        # 5. OpenAI
        if "o1" in m and "mini" not in m:
            return "o1"
        if "o3" in m or "o3-mini" in m:
            return "o3-mini"
        if "gpt-4o-mini" in m:
            return "gpt-4o-mini"
        if "gpt-4o" in m:
            return "gpt-4o"
        if "gpt-4-turbo" in m or "gpt-4-1106" in m or "gpt-4-0125" in m:
            return "gpt-4-turbo"
        if "gpt-3.5" in m:
            return "gpt-3.5-turbo"
        if "gpt-4" in m:
            return "gpt-4o"

        # 6. DeepSeek
        if "deepseek" in m:
            if "reasoner" in m or "r1" in m:
                return "deepseek-reasoner"
            if "coder" in m:
                return "deepseek-coder"
            return "deepseek-chat"

        # 7. Meta Llama
        if "llama" in m:
            if "3.3" in m or "3-3" in m:
                return "llama-3.3-70b"
            if "405b" in m:
                return "llama-3.1-405b"
            if "8b" in m:
                return "llama-3.1-8b"
            if "70b" in m:
                return "llama-3.1-70b"
            return "llama-3.3-70b"

        # 8. Mistral AI
        if "codestral" in m:
            return "codestral"
        if "mistral-large" in m or "mistral-large-2" in m:
            return "mistral-large"
        if "mistral-small" in m:
            return "mistral-small"
        if "mistral" in m or "mixtral" in m:
            return "mistral-large"

        # 9. Alibaba Qwen
        if "qwen" in m:
            if "32b" in m:
                return "qwen-2.5-coder-32b"
            if "7b" in m:
                return "qwen-2.5-coder-7b"
            if "72b" in m:
                return "qwen-2.5-72b"
            if "coder" in m:
                return "qwen-2.5-coder-32b"
            return "qwen-2.5-coder-32b"

        # Direct key matching
        if m in self.models:
            return m

        return "default"

    def calculate_cost(self, raw_model: str, input_tokens: int, output_tokens: int) -> Tuple[float, str]:
        key = self.normalize_model_name(raw_model)
        rate = self.models.get(key, self.models.get("default", {
            "name": "Default",
            "provider": "General",
            "input_per_million": 0.50,
            "output_per_million": 2.00
        }))

        in_rate = rate.get("input_per_million", 0.50) / 1_000_000.0
        out_rate = rate.get("output_per_million", 2.00) / 1_000_000.0

        cost = (input_tokens * in_rate) + (output_tokens * out_rate)
        friendly_name = rate.get("name", key)
        return round(cost, 6), friendly_name
