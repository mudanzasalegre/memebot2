# memebot2/fetcher/pumpfun.py   –  stub temporal «sin Pump Fun»
"""
Pump Fun desactivado: el módulo devuelve siempre una lista vacía
para que el orquestador siga funcionando sin errores de Bitquery.
"""

from typing import List

async def get_latest_pumpfun() -> List[dict]:  # noqa: D401
    """Devuelve [].  Se puede reactivar más adelante sustituyendo este archivo."""
    return []
