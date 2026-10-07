import threading
import time
from typing import Dict, Any

from backend.database import Database
from backend.pricing import PricingEngine
from backend.opencode_collector import OpenCodeCollector
from backend.antigravity_collector import AntigravityCollector
from backend.claude_collector import ClaudeCodeCollector
from backend.continue_collector import ContinueCollector
from backend.aider_collector import AiderCollector
from backend.cursor_collector import CursorWindsurfCollector
from backend.vscode_collector import VSCodeAICollector
from backend.ollama_collector import OllamaCollector

class SyncManager:
    def __init__(self, db: Database, pricing: PricingEngine):
        self.db = db
        self.pricing = pricing
        self.opencode_col = OpenCodeCollector(db, pricing)
        self.antigravity_col = AntigravityCollector(db, pricing)
        self.claude_col = ClaudeCodeCollector(db, pricing)
        self.continue_col = ContinueCollector(db, pricing)
        self.aider_col = AiderCollector(db, pricing)
        self.cursor_col = CursorWindsurfCollector(db, pricing)
        self.vscode_col = VSCodeAICollector(db, pricing)
        self.ollama_col = OllamaCollector(db, pricing)

        self.is_running = False
        self._thread = None
        self.last_sync_time = None
        self.last_sync_result: Dict[str, Any] = {}

    def sync_all(self) -> Dict[str, Any]:
        start = time.time()
        print("[SyncManager] Iniciando sincronización unificada de todos los IDEs...")
        
        opencode_synced = self.opencode_col.sync()
        antigravity_synced = self.antigravity_col.sync()
        claude_synced = self.claude_col.sync()
        continue_synced = self.continue_col.sync()
        aider_synced = self.aider_col.sync()
        cursor_synced = self.cursor_col.sync()
        vscode_synced = self.vscode_col.sync()
        ollama_synced = self.ollama_col.sync()
        
        duration = round(time.time() - start, 2)
        self.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.last_sync_result = {
            "opencode_sessions_synced": opencode_synced,
            "antigravity_sessions_synced": antigravity_synced,
            "claude_sessions_synced": claude_synced,
            "continue_sessions_synced": continue_synced,
            "aider_sessions_synced": aider_synced,
            "cursor_sessions_synced": cursor_synced,
            "vscode_sessions_synced": vscode_synced,
            "ollama_sessions_synced": ollama_synced,
            "total_synced": (
                opencode_synced + antigravity_synced + claude_synced + 
                continue_synced + aider_synced + cursor_synced + 
                vscode_synced + ollama_synced
            ),
            "duration_seconds": duration,
            "timestamp": self.last_sync_time
        }
        print(f"[SyncManager] Sincronización multi-IDE completada en {duration}s. Total sesiones procesadas: {self.last_sync_result['total_synced']}")
        return self.last_sync_result

    def start_background_sync(self, interval_seconds: int = 30):
        if self.is_running:
            return
        self.is_running = True

        def _loop():
            # Initial sync on launch
            try:
                self.sync_all()
            except Exception as e:
                print(f"[SyncManager] Error en sincronización inicial: {e}")

            while self.is_running:
                time.sleep(interval_seconds)
                if not self.is_running:
                    break
                try:
                    self.sync_all()
                except Exception as e:
                    print(f"[SyncManager] Error en ciclo periódico de sincronización: {e}")

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        print(f"[SyncManager] Sincronizador en segundo plano multi-IDE iniciado cada {interval_seconds}s.")

    def stop(self):
        self.is_running = False
