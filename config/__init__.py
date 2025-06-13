"""
Facilita los imports abreviados:

    from config import MAX_AGE_DAYS, MIN_SCORE_TOTAL
    from config import exits

Todos los símbolos definidos en `config.py` y el sub-módulo `exits`
quedan expuestos por defecto.
"""

from __future__ import annotations

# Re-exporta las constantes/funciones de config.py
from .config import *            # noqa: F401,F403
# Y el sub-módulo completo de salidas (para hacer: `from config import exits`)
from . import exits              # noqa: F401

# Limita el wildcard import a lo que venga de config.py + exits
__all__ = [*config.__all__, "exits"]  # type: ignore
