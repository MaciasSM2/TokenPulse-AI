"""
TokenPulse AI - Paquete de Contabilidad de Tokens y Auditoría por Proyecto
Permite vincular proyectos, registrar procesos, auditar consumo de IAs y medir tokens en tiempo real.
"""

from tokenpulse.tracker import TokenTracker, track_usage, get_tracker

__version__ = "1.3.0"
__all__ = ["TokenTracker", "track_usage", "get_tracker", "__version__"]
