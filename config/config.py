# config/config.py
"""
Carga del fichero `.env` + definición de parámetros globales.

Este módulo se importa muy pronto en todo el proyecto; **debe** ser ligero.
Las constantes son inmutables a efectos prácticos, por lo que evitamos
setter dinámico para mayor simplicidad.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ───────────────────────── ROOT & .env ─────────────────────────
ROOT_DIR: Path = Path(__file__).resolve().parent.parent   # …/memebot2
load_dotenv(ROOT_DIR / ".env", override=False)            # una sola vez

# ───────────────────── helpers robustos (env → int/float) ─────
def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).split()[0]
    try:
        return int(raw)
    except ValueError:          # en caso de strings vacíos o no numéricos
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).split()[0]
    try:
        return float(raw)
    except ValueError:
        return default


# ───────────────────────── URLs / API keys ─────────────────────
DEX_API_BASE     : str = os.getenv("DEX_API_BASE", "https://api.dexscreener.com")
PUMPFUN_API_BASE : str = os.getenv("PUMPFUN_API_BASE", "")
RUGCHECK_API_BASE: str = os.getenv("RUGCHECK_API_BASE", "")
HELIUS_API_BASE  : str = os.getenv("HELIUS_API_BASE", "https://api.helius.xyz")
GMGN_API_BASE    : str = os.getenv("GMGN_API_BASE", "https://api.gmgn.ai")

BITQUERY_TOKEN   : str = os.getenv("BITQUERY_TOKEN", "")
RUGCHECK_API_KEY : str = os.getenv("RUGCHECK_API_KEY", "")
HELIUS_API_KEY   : str = os.getenv("HELIUS_API_KEY", "")
GMGN_API_KEY     : str = os.getenv("GMGN_API_KEY", "")

# ───────────────────────── Wallet (firma) ──────────────────────
SOL_PRIVATE_KEY  : str = os.getenv("SOL_PRIVATE_KEY", "")
SOL_PUBLIC_KEY   : str = os.getenv("SOL_PUBLIC_KEY", "")
SOL_RPC_URL      : str = os.getenv("SOL_RPC_URL", "https://api.mainnet-beta.solana.com")

# ───────────────────────── BD & timers ─────────────────────────
SQLITE_DB              : str   = os.getenv("SQLITE_DB", "data/memebotdatabase.db")
SLEEP_SECONDS          : int   = _env_int("SLEEP_SECONDS", 10)
DISCOVERY_INTERVAL     : int   = _env_int("DISCOVERY_INTERVAL", 60)
VALIDATION_BATCH_SIZE  : int   = _env_int("VALIDATION_BATCH_SIZE", 5)

# ───────────────── Filtros de descubrimiento ───────────────────
MAX_AGE_DAYS        : int   = _env_int  ("MAX_AGE_DAYS",        700)
MIN_HOLDERS         : int   = _env_int  ("MIN_HOLDERS",         50)
MIN_LIQUIDITY_USD   : float = _env_float("MIN_LIQUIDITY_USD", 5000.0)
MIN_VOL_USD_24H     : float = _env_float("MIN_VOL_USD_24H",   10000.0)
MAX_24H_VOLUME      : float = _env_float("MAX_24H_VOLUME",  1500000.0)
MIN_SCORE_TOTAL     : int   = _env_int  ("MIN_SCORE_TOTAL",     65)

# ─────────────────── Tamaño de posición ───────────────────────
TRADE_AMOUNT_SOL    : float = _env_float("TRADE_AMOUNT_SOL", 0.0)

# ─────────────────── export control 🔒 ─────────────────────────
__all__ = [
    # helpers
    "_env_int",
    "_env_float",
    # endpoints / keys
    "DEX_API_BASE", "PUMPFUN_API_BASE", "RUGCHECK_API_BASE",
    "HELIUS_API_BASE", "GMGN_API_BASE",
    "BITQUERY_TOKEN", "RUGCHECK_API_KEY", "HELIUS_API_KEY", "GMGN_API_KEY",
    # wallet
    "SOL_PRIVATE_KEY", "SOL_PUBLIC_KEY", "SOL_RPC_URL",
    # db / timers
    "SQLITE_DB", "SLEEP_SECONDS", "DISCOVERY_INTERVAL", "VALIDATION_BATCH_SIZE",
    # filtros
    "MAX_AGE_DAYS", "MIN_HOLDERS", "MIN_LIQUIDITY_USD", "MIN_VOL_USD_24H",
    "MAX_24H_VOLUME", "MIN_SCORE_TOTAL",
    # trading
    "TRADE_AMOUNT_SOL",
]
