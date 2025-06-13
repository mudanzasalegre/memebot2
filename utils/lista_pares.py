# memebot2/utils/lista_pares.py
"""
Mantiene una **lista dinámica** de pares pendientes de analizar y una caché
en disco con los que ya fueron procesados, para evitar llamadas repetidas.

Uso típico:

    from memebot2.utils.lista_pares import agregar_si_nuevo, obtener_pares

Este módulo es **thread-safe** dentro del event-loop: usa sólo estructuras
locales y escrituras append a disco; no hay locks externos.
"""

from __future__ import annotations

import logging
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
BASE_DIR.mkdir(exist_ok=True)
CACHE_FILE = BASE_DIR / "pares_procesados.txt"

_pair_watch: set[str] = set()
_processed: set[str] = set()

# ───────────────────────── helpers internos ───────────────────
def _load_cache() -> set[str]:
    if not CACHE_FILE.exists():
        return set()
    with CACHE_FILE.open() as f:
        return {line.strip() for line in f if line.strip()}


# carga al importar el módulo
_processed.update(_load_cache())


# ───────────────────────── API pública ─────────────────────────
def agregar_si_nuevo(address: str) -> None:
    """Añade `address` a la lista de pendientes si no estaba visto."""
    if address in _processed or address in _pair_watch:
        return
    _pair_watch.add(address)


def obtener_pares() -> list[str]:
    """Devuelve copia de la lista de pares pendientes."""
    return list(_pair_watch)


def eliminar_par(address: str) -> None:
    """
    Saca el par de la lista activa y lo marca como procesado
    (también lo escribe en caché para persistencia entre ejecuciones).
    """
    if address in _pair_watch:
        _pair_watch.discard(address)

    if address not in _processed:
        try:
            with CACHE_FILE.open("a") as f:
                f.write(address + "\n")
        except Exception as e:
            logging.warning("[lista_pares] No se pudo escribir en caché: %s", e)
        _processed.add(address)
