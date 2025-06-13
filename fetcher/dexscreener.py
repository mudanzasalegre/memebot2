# memebot2/fetcher/dexscreener.py
"""
Wrapper minimal de la API DexScreener → dict normalizado.

Devuelve `None` si el par no existe o falla los filtros rápidos
(antigüedad superior a MAX_AGE_DAYS).
"""

from __future__ import annotations

import datetime as _dt

import aiohttp
import pytz
import tenacity

from ..config import DEX_API_BASE, MAX_AGE_DAYS

PAIR_URL = f"{DEX_API_BASE.rstrip('/')}/latest/dex/pairs/solana"


@tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(3))
async def get_pair(pair_id: str) -> dict | None:
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{PAIR_URL}/{pair_id}") as r:
            if r.status == 404:
                return None
            r.raise_for_status()
            data = await r.json()

    # DexScreener puede devolver {"pair": {…}} o {"pairs": [{…}]}
    pair_data = (
        data.get("pair")
        or (data.get("pairs")[0] if data.get("pairs") else None)
    )
    if not pair_data:
        return None

    created_ts = int(pair_data["pairCreatedAt"]) / 1000
    age_days = (
        _dt.datetime.utcnow() - _dt.datetime.utcfromtimestamp(created_ts)
    ).days
    if age_days > MAX_AGE_DAYS:
        return None

    return {
        "address": pair_data["baseToken"]["address"],
        "symbol": pair_data["baseToken"]["symbol"],
        "name": pair_data["baseToken"]["name"],
        "created_at": _dt.datetime.utcfromtimestamp(created_ts).replace(
            tzinfo=pytz.UTC
        ),
        "vol24h": float(pair_data["volume"]["usd"]),
        "liquidity": float(pair_data.get("liquidity", {}).get("usd", 0.0)),
        "holders": int(
            pair_data["txns"]["h24"]["buys"]
            + pair_data["txns"]["h24"]["sells"]
        ),
        "txns_last_5min": int(pair_data["txns"].get("m5", {}).get("buys", 0)),
        # precio spot (USD) por comodidad de la lógica de salidas
        "price_usd": float(pair_data.get("priceUsd") or 0),
    }
