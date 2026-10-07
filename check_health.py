"""
Script de Verificación de Integridad y Diagnóstico Preventivo (TokenPulse AI)
Ejecuta diagnósticos del sistema, bases de datos, dependencias y puertos.
"""

import os
import sys
import sqlite3
import socket
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.config import TRACKER_DB_PATH, OPENCODE_DB_PATH, ANTIGRAVITY_BRAIN_PATH, DEFAULT_PORT
from backend.database import Database
from backend.pricing import PricingEngine
from backend.sync_manager import SyncManager

def check_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def run_diagnostics():
    print("=" * 65)
    print("  🛡️  DIAGNÓSTICO PREVENTIVO Y SALUD DEL SISTEMA - TokenPulse AI")
    print("=" * 65)
    all_ok = True

    # 1. Base de datos central
    print("\n[1/5] Verificando Base de Datos Local (token_tracker.db)...")
    if not TRACKER_DB_PATH.exists():
        print(f"  ⚠️  La base de datos no existe en: {TRACKER_DB_PATH}")
        print("  → Se creará automáticamente al iniciar la sincronización.")
    else:
        try:
            conn = sqlite3.connect(TRACKER_DB_PATH)
            res = conn.cursor().execute("PRAGMA integrity_check;").fetchall()
            conn.close()
            if res == [("ok",)]:
                print(f"  ✓ Integridad SQLite: PERFECTA (PRAGMA integrity_check = ok)")
            else:
                print(f"  ❌ Advertencia de integridad: {res}")
                all_ok = False
        except Exception as e:
            print(f"  ❌ Error accediendo a token_tracker.db: {e}")
            all_ok = False

    # 2. Origen OpenCode
    print("\n[2/5] Verificando Almacén de OpenCode Desktop...")
    if OPENCODE_DB_PATH.exists():
        try:
            conn = sqlite3.connect(f"file:{OPENCODE_DB_PATH}?mode=ro", uri=True)
            cnt = conn.cursor().execute("SELECT count(*) FROM session;").fetchone()[0]
            conn.close()
            print(f"  ✓ Conexión OpenCode OK: {cnt} sesiones accesibles en modo lectura.")
        except Exception as e:
            print(f"  ⚠️  Aviso en OpenCode DB: {e}")
    else:
        print(f"  ℹ️  No se detectó opencode.db en {OPENCODE_DB_PATH} (normal si no se usa OpenCode).")

    # 3. Origen Antigravity IDE
    print("\n[3/5] Verificando Transcripciones de Antigravity IDE...")
    if ANTIGRAVITY_BRAIN_PATH.exists():
        conv_dirs = [d for d in ANTIGRAVITY_BRAIN_PATH.iterdir() if d.is_dir()]
        print(f"  ✓ Directorio Brain OK: {len(conv_dirs)} carpetas de conversaciones detectadas.")
    else:
        print(f"  ❌ Directorio brain de Antigravity no encontrado en: {ANTIGRAVITY_BRAIN_PATH}")
        all_ok = False

    # 4. Estado de Puerto y Servidor
    print(f"\n[4/5] Verificando Puerto de Red ({DEFAULT_PORT})...")
    is_running = check_port_in_use(DEFAULT_PORT)
    if is_running:
        print(f"  🟢 El servidor Dashboard YA ESTÁ CORRIENDO en http://localhost:{DEFAULT_PORT}")
    else:
        print(f"  ⚪ El puerto {DEFAULT_PORT} está LIBRE (Listo para iniciar con 'python main.py')")

    # 5. Prueba de Sincronización
    print("\n[5/5] Probando Prueba Rápida de Sincronización...")
    try:
        db = Database()
        pricing = PricingEngine()
        manager = SyncManager(db, pricing)
        sync_res = manager.sync_all()
        stats = db.get_summary_stats()
        print(f"  ✓ Sincronización exitosa en {sync_res['duration_seconds']}s")
        print(f"  • Sesiones Consolidadas: {stats['overall']['total_sessions']}")
        print(f"  • Tokens Totales:        {stats['overall']['total_tokens']:,}")
        print(f"  • Gasto Acumulado:       ${stats['overall']['total_cost_usd']:.4f} USD")
    except Exception as e:
        print(f"  ❌ Error en sincronización: {e}")
        all_ok = False

    print("\n" + "=" * 65)
    if all_ok:
        print("  ✅ ESTADO GENERAL: SISTEMA 100% OPERATIVO Y RESILIENTE")
    else:
        print("  ⚠️  ESTADO GENERAL: SE DETECTARON ADVERTENCIAS (Revisar logs arriba)")
    print("=" * 65)

if __name__ == "__main__":
    run_diagnostics()
