"""
analytics/trend.py
──────────────────
Señal muy ligera de tendencia:

• Usa dos EMAs (rápida y lenta) sobre el historial de precio DexScreener
  (limit=200 puntos) para clasificar en: "up", "down", "flat".

El endpoint devuelve velas de 5 min — suficiente para un sniper
que rota posiciones en minutos-horas.

Si la petición falla ⇒ devuelve 'unknown' (tratado como score neutro).
"""

from __future__ import annotations

import asyncio
import logging
from statistics import mean
from typing import Literal

import aiohttp
import tenacity

from ..config import DEX_API_BASE

log = logging.getLogger("trend")

EMA_FAST = 7    # velas
EMA_SLOW = 21


def _ema(series: list[float], length: int) -> float:
    """
    Calcula la EMA simple (peso exponencial) de la lista `series`
    usando la fórmula recursiva.  No dependemos de pandas para
    evitar peso extra.
    """
    if len(series) < length:
        return mean(series) if series else 0.0

    k = 2 / (length + 1)
    ema = series[0]
    for price in series[1:]:
        ema = price * k + ema * (1 - k)
    return ema


@tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(3))
async def _prices(address: str) -> list[float]:
    """
    Devuelve lista de cierres (USD) de 5 min del token.
    DexScreener endpoint no documentado pero estable.
    """
    url = (
        f"{DEX_API_BASE.rstrip('/')}/chart/"
        f"solana/{address}?interval=5m&limit=200"
    )
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            if r.status != 200:
                raise RuntimeError(f"Status {r.status}")
            data = await r.json()

    # `data` es lista de dicts con "close"
    return [float(c["close"]) for c in data if c.get("close")]


async def trend_signal(address: str) -> Literal["up", "down", "flat", "unknown"]:
    """
    Clasifica la tendencia actual del token.
    """
    try:
        closes = await _prices(address)
    except Exception as e:
        log.debug("[trend] %s fetch error: %s", address[:4], e)
        return "unknown"

    if len(closes) < EMA_SLOW:
        return "unknown"          # sin histórico suficiente

    fast = _ema(closes[-EMA_FAST * 3 :], EMA_FAST)
    slow = _ema(closes[-EMA_SLOW * 3 :], EMA_SLOW)

    if fast > slow * 1.02:
        return "up"
    if fast < slow * 0.98:
        return "down"
    return "flat"


# Quick CLI test:  python -m memebot2.analytics.trend <token-address>
if __name__ == "__main__":
    import sys

    async def _t():
        addr = sys.argv[1]
        print(await trend_signal(addr))

    asyncio.run(_t())
