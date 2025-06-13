# memebot2/utils/descubridor_pares.py
"""
Scraper ultra-ligero de DexScreener que lista tokens *recién creados* en la
red Solana.  Sólo aplica el filtro de antigüedad (`MAX_AGE_DAYS`); el resto de
filtros los ejecuta `analytics.filters` posterior.

Devuelve una lista con los **mint addresses** candidatos.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import List

import aiohttp

from ..config import DEX_API_BASE, MAX_AGE_DAYS

log = logging.getLogger("descubridor")
log.setLevel(logging.DEBUG)

DEX = DEX_API_BASE.rstrip("/")
URLS = [
    f"{DEX}/token-profiles/latest/v1?chainId=solana&limit=500",
    f"{DEX}/token-profiles/latest?chainId=solana&limit=500",
    f"{DEX}/latest/dex/tokens/solana?limit=500",
]


# ---------------------------- helpers --------------------------
def _to_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


async def _json(s: aiohttp.ClientSession, url: str):
    try:
        async with s.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}) as r:
            if r.status == 404:
                return None
            r.raise_for_status()
            return await r.json()
    except Exception:
        return None


def _items(raw) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for k in ("pairs", "tokens", "dexTokens", "data"):
            if isinstance(raw.get(k), list):
                return raw[k]
    return []


# ---------------------- función principal ----------------------
async def fetch_candidate_pairs() -> List[str]:
    """
    Escanea los 3 endpoints públicos y extrae los mint-addresses cuya edad
    (en días) sea ≤ MAX_AGE_DAYS.

    Devuelve lista sin duplicados.
    """
    async with aiohttp.ClientSession() as s:
        raw = None
        for u in URLS:
            raw = await _json(s, u)
            if raw:
                log.debug("DexScreener OK → %s", u.split(DEX)[1])
                break
        if not raw:
            log.error("DexScreener: ningún endpoint disponible")
            return []

    out = []
    for t in _items(raw):
        addr = (
            t.get("tokenAddress")
            or t.get("baseToken", {}).get("address")
            or t.get("address")
        )
        if not addr:
            continue

        age = _to_float(t.get("ageDays") or t.get("age"), 99)
        log.debug("⏱ %s age=%.1f", addr[:4], age)

        if age <= MAX_AGE_DAYS:
            out.append(addr)

    log.info("Descubridor: %s candidatos", len(out))
    return out


# Quick CLI test:  python -m memebot2.utils.descubridor_pares
if __name__ == "__main__":
    async def _test():
        lst = await fetch_candidate_pairs()
        print(len(lst), lst[:10])

    asyncio.run(_test())
