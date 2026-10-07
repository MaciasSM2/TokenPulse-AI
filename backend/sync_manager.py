import threading
import time
from typing import Dict, Any

from backend.database import Database
from backend.pricing import PricingEngine
from backend.opencode_collector import OpenCodeCollector
from backend.antigravity_collector import AntigravityCollector

class SyncManager:
    def __init__(self, db: Database, pricing: PricingEngine):
        self.db = db
        self.pricing = pricing
        self.opencode_col = OpenCodeCollector(db, pricing)
        self.antigravity_col = AntigravityCollector(db, pricing)
        self.is_running = False
        self._thread = None
        self.last_sync_time = None
        self.last_sync_result: Dict[str, Any] = {}

    def sync_all(self) -> Dict[str, Any]:
        start = time.time()
        print("[SyncManager] Iniciando sincronización unificada...")
        
        opencode_synced = self.opencode_col.sync()
        antigravity_synced = self.antigravity_col.sync()
        
        duration = round(time.time() - start, 2)
        self.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.last_sync_result = {
            "opencode_sessions_synced": opencode_synced,
            "antigravity_sessions_synced": antigravity_synced,
            "duration_seconds": duration,
            "timestamp": self.last_sync_time
        }
        print(f"[SyncManager] Sincronización completada en {duration}s. OpenCode: {opencode_synced}, Antigravity: {antigravity_synced}")
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
        print(f"[SyncManager] Sincronizador en segundo plano iniciado cada {interval_seconds}s.")

    def stop(self):
        self.is_running = False
