import argparse
import sys
import uvicorn
from pathlib import Path

# Fix Windows console encoding for UTF-8 characters
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.config import DEFAULT_HOST, DEFAULT_PORT
from backend.database import Database
from backend.pricing import PricingEngine
from backend.sync_manager import SyncManager

def run_sync_cli():
    print("=" * 60)
    print("  TokenPulse AI - Sincronizador de Tokens & Gasto")
    print("=" * 60)
    db = Database()
    pricing = PricingEngine()
    manager = SyncManager(db, pricing)
    res = manager.sync_all()
    stats = db.get_summary_stats()
    ov = stats["overall"]

    print("\n[Resumen Consolidado]")
    print(f"  • Sesiones Totales:       {ov['total_sessions']}")
    print(f"  • Tokens de Entrada:      {ov['total_input_tokens']:,}")
    print(f"  • Tokens de Salida:       {ov['total_output_tokens']:,}")
    print(f"  • Tokens de Razonamiento: {ov['total_reasoning_tokens']:,}")
    print(f"  • Tokens Totales:         {ov['total_tokens']:,}")
    print(f"  • Gasto Total Estimado:   ${ov['total_cost_usd']:.4f} USD\n")

    print("[Por Entorno]")
    for ide in stats["by_ide"]:
        name = "Antigravity IDE" if ide["source_ide"] == "antigravity" else "OpenCode Desktop"
        print(f"  • {name:18}: {ide['sessions']} sesiones | {ide['tokens']:,} tokens | ${ide['cost_usd']:.4f} USD")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="TokenPulse AI - Contador de Tokens & Costes")
    parser.add_argument("--sync-only", action="store_true", help="Solo sincronizar y mostrar resumen en consola sin iniciar servidor")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host del servidor (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Puerto del servidor (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    if args.sync_only:
        run_sync_cli()
        return

    # Run quick initial sync in CLI
    run_sync_cli()

    print(f"\n[🚀 Iniciando Servidor Web Dashboard]")
    print(f"  URL Local: http://localhost:{args.port}")
    print(f"  Presiona Ctrl+C para detener el servidor.\n")

    uvicorn.run("backend.app:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
